import asyncio
import json
import uuid
from typing import Any

from django.core.cache import cache
from django.urls import reverse

from apps.director.models import Meeting, Question
from apps.meeting import utils
from apps.meeting.base import BaseMeetingConsumer
from apps.meeting.constants import CloseCodes, GroupPrefixes, MessageTypes
from apps.meeting.models import Response

# ! SECURITY WARNING: In production, session ID must NOT be passed through URL parameters
# TODO: Implement secure session handling mechanism before production deployment
# ? Consider using JWT tokens or secure headers for authentication


class HostMeetingConsumer(BaseMeetingConsumer):
    """
    WebSocket consumer for meeting hosts.

    Handles host-specific operations including:
    - Meeting lifecycle management (start/end)
    - Question distribution to participants
    - Real-time participant tracking
    - Meeting duration and statistics tracking
    """

    async def connect(self) -> None:
        """
        Establishes WebSocket connection for meeting host.

        Performs authentication, meeting validation, and initial setup.
        Connection is rejected if any validation fails.
        """
        # NOTE: Validate URL routing accessibility
        url_route_data: dict[str, Any] | None = self._get_url_route()
        if not url_route_data:
            await self._close_with_log(
                code=CloseCodes.NO_URL_ROUTE.code,
                message=CloseCodes.NO_URL_ROUTE.message,
            )
            return

        self.meeting_uuid: uuid.UUID = url_route_data["kwargs"]["meeting_id"]

        # NOTE: Extract session ID from query parameters for authentication
        session_identifier: str | None = self._get_session_id_from_query()
        if not session_identifier:
            await self._close_with_log(
                code=CloseCodes.NO_SESSION.code, message=CloseCodes.NO_SESSION.message
            )
            return

        # NOTE: Validate user authentication through session
        authenticated_user = await utils.get_user_from_session(session_identifier)
        if authenticated_user is None or not authenticated_user.is_authenticated:
            await self._close_with_log(
                code=CloseCodes.AUTH_FAILED.code, message=CloseCodes.AUTH_FAILED.message
            )
            return
        
        self.user = authenticated_user

        # NOTE: Retrieve meeting data with associated questions
        meeting_data_bundle: (
            utils.MeetingData | None
        ) = await utils.get_meeting_with_questions(meeting_id=self.meeting_uuid)
        if not meeting_data_bundle:
            await self._close_with_log(
                message=CloseCodes.NO_MEETING.message, code=CloseCodes.NO_MEETING.code
            )
            return

        # NOTE: Initialize meeting-specific attributes
        self.meeting_access_code: str = meeting_data_bundle.access_code
        self.allocated_meeting_duration_seconds: int = (
            meeting_data_bundle.meeting.duration
        )
        self.active_participant_count: int = 0
        self.total_responses_count: int = 0

        # NOTE: Ensure meeting has questions before proceeding
        if not meeting_data_bundle.questions:
            await self._close_with_log(
                code=CloseCodes.NO_QUESTIONS.code,
                message=CloseCodes.NO_QUESTIONS.message,
            )
            return

        # NOTE: Accept connection before performing any group operations
        await self.accept()

        # NOTE: Initialize meeting lock status in cache (prevents late joins)
        await cache.aset(
            key=f"{GroupPrefixes.MEETING_LOCKED}{self.meeting_access_code}",
            value=False,
            timeout=3600,  # ? Consider making cache timeout configurable
        )

        # NOTE: Add host to dedicated channel group for real-time communication
        self.host_channel_group_name: str = (
            f"{GroupPrefixes.HOST}{self.meeting_access_code}"
        )
        await self.channel_layer.group_add(
            group=self.host_channel_group_name, channel=self.channel_name
        )

        # NOTE: Extract question descriptions for frontend transmission
        question_descriptions_list: list[str] = [
            question.description for question in meeting_data_bundle.questions
        ]

        # NOTE: Send initial meeting data to host frontend
        await self._send_json(
            data={
                "type": MessageTypes.START_MEETING,
                "questions": question_descriptions_list,
                "access_code": self.meeting_access_code,
            }
        )

        self.total_questions_presented: int = 1

        # NOTE: Initialize participant username tracking cache
        await cache.aset(
            key=utils.get_username_cache_key(self.meeting_access_code), value=[]
        )

    async def disconnect(self, code: int) -> None:
        """
        Handles host disconnection cleanup.

        Args:
            close_code: WebSocket close code indicating disconnection reason
        """
        # NOTE: Remove host from channel group if access code exists
        if hasattr(self, "meeting_access_code") and self.meeting_access_code:
            await self.channel_layer.group_discard(
                f"{GroupPrefixes.HOST}{self.meeting_access_code}", self.channel_name
            )

        # NOTE: Notify all participants that meeting has ended
        await self.channel_layer.group_send(
            group=f"{GroupPrefixes.PARTICIPANT}{self.meeting_access_code}",
            message={"type": MessageTypes.END_MEETING},
        )

        # NOTE: Clean up all meeting-related cache entries
        await cache.adelete(
            key=f"{GroupPrefixes.MEETING_LOCKED}{self.meeting_access_code}"
        )
        await cache.adelete(key=utils.get_username_cache_key(self.meeting_access_code))

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        """
        Processes incoming WebSocket messages from host frontend.

        Args:
            text_data: JSON string containing message data
            bytes_data: Binary data (not used in this implementation)
        """
        if not text_data:
            return

        try:
            parsed_message_data: dict[str, Any] = json.loads(text_data)
            message_type_identifier: str = parsed_message_data["type"]

            # NOTE: Route message to appropriate handler based on type
            match message_type_identifier:
                case MessageTypes.START_MEETING:
                    await self.handle_start_meeting(event=parsed_message_data)
                case MessageTypes.NEXT_QUESTION:
                    await self.handle_next_question(event=parsed_message_data)
                case MessageTypes.END_MEETING:
                    await self.handle_end_meeting(event=parsed_message_data)
        except json.JSONDecodeError:
            # ! JSON parsing failed - consider logging this in production
            pass

    async def handle_start_meeting(self, event: dict[str, Any]) -> None:
        """
        Initiates the meeting session.

        Locks meeting to prevent new participants and starts timing mechanisms.

        Args:
            event: Message event containing meeting start data
        """
        # NOTE: Lock meeting to prevent additional participants from joining
        await cache.aset(
            key=f"{GroupPrefixes.MEETING_LOCKED}{self.meeting_access_code}", value=True
        )

        # NOTE: Create background task to auto-end meeting after duration limit
        self.meeting_auto_end_timer = asyncio.create_task(
            self._auto_end_meeting_after_duration(
                self.allocated_meeting_duration_seconds
            )
        )

        # NOTE: Create background task to track actual meeting duration
        self.meeting_duration_tracking_timer = asyncio.create_task(
            utils.meeting_duration_counter()
        )

        # NOTE: Distribute first question to all connected participants
        first_question_text: str = event.get("question", "")
        if first_question_text:
            await self.channel_layer.group_send(
                group=f"{GroupPrefixes.PARTICIPANT}{self.meeting_access_code}",
                message={
                    "type": MessageTypes.START_MEETING,
                    "question": first_question_text,
                },
            )

    async def _auto_end_meeting_after_duration(self, duration_minutes: int) -> None:
        """
        Automatically ends meeting after specified duration.

        Args:
            duration_minutes: Maximum meeting duration in minutes

        Note:
            This is a background task that can be cancelled if meeting ends early.
        """
        try:
            # NOTE: Convert minutes to seconds for asyncio.sleep
            await asyncio.sleep(duration_minutes * 60)
            await self.handle_end_meeting({"type": MessageTypes.END_MEETING})
        except asyncio.CancelledError:
            # NOTE: Task was cancelled intentionally (meeting ended early)
            pass

    async def handle_end_meeting(self, event: dict[str, Any]) -> None:
        """
        Terminates the meeting session and performs cleanup.

        Cancels timers, updates meeting statistics, and notifies all participants.

        Args:
            event: Message event containing meeting end data
        """
        # NOTE: Cancel auto-end timer if still active
        if (
            hasattr(self, "meeting_auto_end_timer")
            and self.meeting_auto_end_timer
            and not self.meeting_auto_end_timer.done()
        ):
            self.meeting_auto_end_timer.cancel()
            try:
                await self.meeting_auto_end_timer
            except asyncio.CancelledError:
                pass

        # NOTE: Cancel duration tracking timer and capture final duration
        if (
            hasattr(self, "meeting_duration_tracking_timer")
            and self.meeting_duration_tracking_timer
        ):
            self.meeting_duration_tracking_timer.cancel()
            try:
                actual_duration_seconds: int = (
                    await self.meeting_duration_tracking_timer
                )
                self.allocated_meeting_duration_seconds = actual_duration_seconds
            except asyncio.CancelledError:
                pass

        # NOTE: Persist meeting statistics to database
        await utils.set_meeting_duration_seconds_field(
            meeting_access_code=self.meeting_access_code,
            duration_seconds=self.allocated_meeting_duration_seconds,
        )
        await utils.set_participant_count(
            meeting_access_code=self.meeting_access_code,
            participant_count=self.active_participant_count,
        )
        await utils.set_total_questions_asked(
            meeting_access_code=self.meeting_access_code,
            questions_presented_count=self.total_questions_presented,
        )

        # NOTE: Update the user's model with the new meeting stats
        self.user.meetings_created_count += 1
        self.user.total_participants_count += self.active_participant_count
        self.user.total_responses_count += self.total_responses_count
        await self.user.asave()


        # NOTE: Send meeting completion notification to host frontend
        await self._send_json(
            data={
                "type": MessageTypes.END_MEETING,
                "url": f"{
                    reverse(
                        viewname='post-meeting-host',
                        kwargs={'meeting_id': str(self.meeting_uuid)},
                    )
                }",
            }
        )

        # NOTE: Notify all participants that meeting has ended
        await self.channel_layer.group_send(
            group=f"{GroupPrefixes.PARTICIPANT}{self.meeting_access_code}",
            message={"type": MessageTypes.END_MEETING},
        )

        await self._close_with_log(message="Meeting successfully terminated")

    async def handle_next_question(self, event: dict[str, Any]) -> None:
        """
        Distributes the next question to all participants.

        Args:
            event: Message event containing next question data
        """
        next_question_text: str = event.get("question", "")
        if next_question_text:
            await self.channel_layer.group_send(
                group=f"{GroupPrefixes.PARTICIPANT}{self.meeting_access_code}",
                message={
                    "type": MessageTypes.NEXT_QUESTION,
                    "question": next_question_text,
                },
            )
        self.total_questions_presented += 1

    async def answer_submitted(self, event: dict[str, Any]) -> None:
        """
        Handles notification when a participant submits an answer.

        Args:
            event: Message event containing answer submission data
        """
        self.total_responses_count += 1
        await self._send_json(data={"type": MessageTypes.ANSWER_SUBMITTED})

    async def participant_joined(self, event: dict[str, Any]) -> None:
        """
        Handles participant joining the meeting.

        Updates participant count and notifies host frontend.

        Args:
            event: Message event containing participant join data
        """
        participant_channel_name = event.get("participant_channel")
        participant_display_name = event.get("participant_name")

        if participant_channel_name and participant_display_name:
            self.active_participant_count += 1
            await self._send_json(
                data={
                    "type": MessageTypes.PARTICIPANT_JOINED,
                    "participant": {
                        "name": participant_display_name,
                        "status": "Connected",
                    },
                }
            )

    async def participant_left(self, event: dict[str, Any]) -> None:
        """
        Handles participant leaving the meeting.

        Args:
            event: Message event containing participant departure data
        """
        departing_participant_name = event.get("name")
        if departing_participant_name:
            await self._send_json(
                data={
                    "type": MessageTypes.PARTICIPANT_LEFT,
                    "name": departing_participant_name,
                }
            )


class ParticipantMeetingConsumer(BaseMeetingConsumer):
    """
    WebSocket consumer for meeting participants.

    Handles participant-specific operations including:
    - Joining meetings with unique username assignment
    - Receiving questions from host
    - Submitting answers to questions
    - Graceful disconnection handling
    """

    async def connect(self) -> None:
        """
        Establishes WebSocket connection for meeting participant.

        Validates meeting availability and prevents joining locked meetings.
        """
        # NOTE: Validate URL routing accessibility
        url_route_data: dict[str, Any] | None = self._get_url_route()
        if not url_route_data:
            await self._close_with_log(
                code=CloseCodes.NO_URL_ROUTE.code,
                message=CloseCodes.NO_URL_ROUTE.message,
            )
            return

        # NOTE: Accept connection immediately for participant
        await self.accept()

        self.meeting_access_code: str = url_route_data["kwargs"]["access_code"]

        # ! CRITICAL: Immediately reject connection if meeting is already locked
        is_meeting_locked = await cache.aget(
            key=f"{GroupPrefixes.MEETING_LOCKED}{self.meeting_access_code}"
        )
        if is_meeting_locked:
            await self.close(code=4401, reason="meeting_locked")
            return

        # NOTE: Initialize channel group identifiers
        self.participant_channel_group_name: str = (
            f"{GroupPrefixes.PARTICIPANT}{self.meeting_access_code}"
        )
        self.host_channel_group_name: str = (
            f"{GroupPrefixes.HOST}{self.meeting_access_code}"
        )

    async def disconnect(self, code: int) -> None:
        """
        Handles participant disconnection cleanup.

        Args:
            code: WebSocket close code indicating disconnection reason
        """
        # NOTE: Notify host that participant has left
        if hasattr(self, "host_channel_group_name") and self.host_channel_group_name:
            await self.channel_layer.group_send(
                group=self.host_channel_group_name,
                message={
                    "type": MessageTypes.PARTICIPANT_LEFT,
                    "name": self.participant_display_name,
                },
            )

        # NOTE: Remove participant from channel group
        if (
            hasattr(self, "participant_channel_group_name")
            and self.participant_channel_group_name
        ):
            await self.channel_layer.group_discard(
                self.participant_channel_group_name, self.channel_name
            )

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        """
        Processes incoming WebSocket messages from participant frontend.

        Args:
            text_data: JSON string containing message data
            bytes_data: Binary data (not used in this implementation)
        """
        if not text_data:
            return

        try:
            parsed_message_data: dict[str, Any] = json.loads(text_data)
            message_type_identifier: str = parsed_message_data["type"]

            # NOTE: Route message to appropriate handler based on type
            match message_type_identifier:
                case MessageTypes.PARTICIPANT_JOINED:
                    # NOTE: This is received immediately after connection establishment
                    await self.handle_participant_joined(event=parsed_message_data)
                case MessageTypes.SUBMIT_ANSWER:
                    await self.handle_submit_answer(event=parsed_message_data)
        except json.JSONDecodeError:
            # ! JSON parsing failed - consider logging this in production
            pass

    async def start_meeting(self, event: dict[str, Any]) -> None:
        """
        Handles meeting start notification from host.

        Args:
            event: Message event containing meeting start data and first question
        """
        first_question_text = event.get("question", "")
        await self._send_json(
            data={"type": MessageTypes.START_MEETING, "question": first_question_text}
        )

    async def end_meeting(self, event: dict[str, Any]) -> None:
        """
        Handles meeting end notification from host.

        Args:
            event: Message event containing meeting end data
        """
        # NOTE: Provide redirect URL for frontend navigation
        await self._send_json(
            data={"type": MessageTypes.END_MEETING, "url": f"{reverse('post-meeting')}"}
        )
        await self.close()

    async def next_question(self, event: dict[str, Any]) -> None:
        """
        Handles next question distribution from host.

        Args:
            event: Message event containing next question data
        """
        next_question_text = event.get("question", "")
        await self._send_json(
            data={"type": MessageTypes.NEXT_QUESTION, "question": next_question_text}
        )

    async def handle_participant_joined(self, event: dict[str, Any]) -> None:
        """
        Processes participant joining the meeting.

        Handles username uniqueness, updates participant lists, and notifies host.

        Args:
            event: Message event containing participant join data
        """
        requested_username: str | None = event.get("name", None)
        if not requested_username:
            # ! This should never happen but provides safety check
            await self._close_with_log(message="Participant username not provided")
            return

        # NOTE: Retrieve current participant usernames from cache
        existing_usernames_list: list[str] | None = await cache.aget(
            key=utils.get_username_cache_key(self.meeting_access_code)
        )
        if existing_usernames_list is None:
            await self._close_with_log(
                message="Participant joined before host established meeting", code=4004
            )
            return

        # NOTE: Handle username conflicts by appending number suffix
        username_conflict_count: int = sum(
            existing_name == requested_username
            or existing_name.startswith(f"{requested_username}(")
            for existing_name in existing_usernames_list
        )

        if username_conflict_count > 0:
            self.participant_display_name: str = (
                f"{requested_username}({username_conflict_count})"
            )
            # NOTE: Inform frontend of modified username
            await self._send_json(
                data={
                    "type": MessageTypes.UPDATE_NAME,
                    "name": self.participant_display_name,
                }
            )
        else:
            self.participant_display_name: str = requested_username

        # NOTE: Update cached username list with new participant
        existing_usernames_list.append(self.participant_display_name)
        await cache.aset(
            key=utils.get_username_cache_key(self.meeting_access_code),
            value=existing_usernames_list,
            timeout=3600,  # ? Consider making cache timeout configurable
        )

        # NOTE: Add participant to channel group for message broadcasting
        await self.channel_layer.group_add(
            group=self.participant_channel_group_name, channel=self.channel_name
        )

        # NOTE: Notify host of new participant
        await self.channel_layer.group_send(
            group=self.host_channel_group_name,
            message={
                "type": MessageTypes.PARTICIPANT_JOINED,
                "participant_name": self.participant_display_name,
                "participant_channel": self.channel_name,
            },
        )

    async def handle_submit_answer(self, event: dict[str, Any]) -> None:
        """
        Processes answer submission from participant.

        Validates answer data, creates response record, and notifies host.

        Args:
            event: Message event containing answer submission data
        """
        # NOTE: Extract answer and question data from event
        submitted_answer_text: str | None = event.get("answer", None)
        associated_question_description: str | None = event.get("question", None)

        if not submitted_answer_text or not associated_question_description:
            await self._send_json(data={"type": MessageTypes.SUBMIT_ERROR})
            return

        # NOTE: Retrieve meeting object for answer association
        meeting_instance: Meeting | None = await utils.get_meeting_by_access_code(
            access_code=self.meeting_access_code
        )
        if not meeting_instance:
            # ! This should never happen in normal operation
            await self._send_json(data={"type": MessageTypes.SUBMIT_ERROR})
            return

        # NOTE: Retrieve question object for answer association
        question_instance: Question | None = await utils.get_question(
            question_description=associated_question_description,
            meeting_instance=meeting_instance,
        )
        if not question_instance:
            # ! This should never happen in normal operation
            await self._send_json(data={"type": MessageTypes.SUBMIT_ERROR})
            return

        # NOTE: Create response model instance
        response_instance: Response | None = await utils.create_response_model(
            meeting_instance=meeting_instance,
            question_instance=question_instance,
            participant_response_text=submitted_answer_text,
        )
        if not response_instance:
            # NOTE: Answer validation failed (invalid content)
            await self._send_json(data={"type": MessageTypes.INVALID_ANSWER})
            return

        # NOTE: Persist response to database
        await response_instance.asave()

        # NOTE: Notify host that valid answer was submitted
        await self.channel_layer.group_send(
            group=f"{GroupPrefixes.HOST}{self.meeting_access_code}",
            message={"type": MessageTypes.ANSWER_SUBMITTED},
        )
