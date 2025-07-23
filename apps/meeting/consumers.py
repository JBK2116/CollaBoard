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

"""
HOST CONSUMER HERE
"""


# IMPORTANT: IN PRODUCTION SESSIONID MUST NOT BE PASSED THROUGH A URL PARAMETER
# IT WILL BE HANDLED LATER...
class HostMeetingConsumer(BaseMeetingConsumer):
    async def connect(self) -> None:
        # 1: Ensure url route is accessible
        url_route: dict[str, Any] | None = self._get_url_route()
        if not url_route:
            await self._close_with_log(
                code=CloseCodes.NO_URL_ROUTE.code,
                message=CloseCodes.NO_URL_ROUTE.message,
            )
            return

        self.meeting_id: uuid.UUID = url_route["kwargs"]["meeting_id"]

        # 2: Get session ID from query parameters (Used for authentication)
        session_id: str | None = self._get_session_id_from_query()
        if not session_id:
            await self._close_with_log(
                code=CloseCodes.NO_SESSION.code, message=CloseCodes.NO_SESSION.message
            )
            return

        # 3: Get user from session (More authentication)
        user = await utils.get_user_from_session(session_id)
        if user is None or not user.is_authenticated:
            await self._close_with_log(
                code=CloseCodes.AUTH_FAILED.code, message=CloseCodes.AUTH_FAILED.message
            )
            return

        # 4: Get meeting and its associated data
        meeting_data: utils.MeetingData | None = await utils.get_meeting_with_questions(
            meeting_id=self.meeting_id
        )
        if not meeting_data:
            await self._close_with_log(
                message=CloseCodes.NO_MEETING.message, code=CloseCodes.NO_MEETING.code
            )
            return
        self.access_code: str = meeting_data.access_code
        self.meeting_duration: int = meeting_data.meeting.duration
        self.participant_count: int = 0

        # 5: Ensure questions exist
        if not meeting_data.questions:
            await self._close_with_log(
                code=CloseCodes.NO_QUESTIONS.code,
                message=CloseCodes.NO_QUESTIONS.message,
            )
            return

        # Accept connection before any group operations
        await self.accept()
        # 6: Cache -> Create meeting_locked key to be used later
        await cache.aset(
            key=f"{GroupPrefixes.MEETING_LOCKED}{self.access_code}",
            value=False,
            timeout=3600,
        )
        # 7: Add The Host to their dedicated channel group
        self.group_name: str = f"{GroupPrefixes.HOST}{self.access_code}"
        await self.channel_layer.group_add(
            group=self.group_name, channel=self.channel_name
        )

        # Get all meeting question descriptions
        questions: list[str] = [q.description for q in meeting_data.questions]

        # 8: Send all questions to the host frontend
        await self._send_json(
            data={
                "type": MessageTypes.START_MEETING,
                "questions": questions,
                "access_code": self.access_code,
            }
        )

        # 9: Cache -> Create usernames cache to track participant usernames
        await cache.aset(key=utils.get_username_cache_key(self.access_code), value=[])

    async def disconnect(self, code: int) -> None:
        # Remove Host from group if access_code exists
        if hasattr(self, "access_code") and self.access_code:
            await self.channel_layer.group_discard(
                f"{GroupPrefixes.HOST}{self.access_code}", self.channel_name
            )
        # Trigger end meeting for all participants
        await self.channel_layer.group_send(
            group=f"{GroupPrefixes.PARTICIPANT}{self.access_code}",
            message={"type": MessageTypes.END_MEETING},
        )
        # Clear all created caches
        await cache.adelete(key=f"{GroupPrefixes.MEETING_LOCKED}{self.access_code}")
        await cache.adelete(key=utils.get_username_cache_key(self.access_code))

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        if not text_data:
            return

        try:
            text_data_json: dict[str, Any] = json.loads(text_data)
            message_type: str = text_data_json["type"]
            # Handle response accordingly
            match message_type:
                case MessageTypes.START_MEETING:
                    await self.start_meeting(event=text_data_json)
                case MessageTypes.NEXT_QUESTION:
                    await self.next_question(event=text_data_json)
                case MessageTypes.END_MEETING:
                    await self.end_meeting(event=text_data_json)
        except json.JSONDecodeError:
            pass  # For now

    # HANDLER METHODS FOR HOST CONSUMER
    async def start_meeting(self, event: dict[str, Any]) -> None:
        # Lock the meeting so no one else can join
        await cache.aset(
            key=f"{GroupPrefixes.MEETING_LOCKED}{self.access_code}", value=True
        )
        # Create timer to end the meeting if it exceeds the allowed duration
        self.end_meeting_timer = asyncio.create_task(
            self.end_meeting_after_duration(self.meeting_duration)
        )
        # Create timer to track actual meeting duration
        self.meeting_duration_timer = asyncio.create_task(
            utils.meeting_duration_counter()
        )
        # Send the first question to all participants
        question: str = event.get("question", "")
        if question:
            await self.channel_layer.group_send(
                group=f"{GroupPrefixes.PARTICIPANT}{self.access_code}",
                message={"type": MessageTypes.START_MEETING, "question": question},
            )

    async def end_meeting_after_duration(self, duration: int) -> None:
        """
        Sends an `end` meeting message to both frontends after duration time is elapsed
        DURATION MUST BE IN MINUTES
        """
        try:
            await asyncio.sleep(duration * 60)
            await self.end_meeting({"type": MessageTypes.END_MEETING})
        except asyncio.CancelledError:
            pass  # Cancelled on purpose

    async def end_meeting(self, event: dict[str, Any]) -> None:
        # Cancel the end meeting timer if it's still running
        if (
            hasattr(self, "end_meeting_timer")
            and self.end_meeting_timer
            and not self.end_meeting_timer.done()
        ):
            # NOTE: Cancel all timers
            self.end_meeting_timer.cancel()
            try:
                await self.end_meeting_timer  # let it cancel
            except asyncio.CancelledError:
                pass  # Timer successfully cancelled
        # Cancel the meeting duration timer
        if (hasattr(self, "meeting_duration_timer") and self.meeting_duration_timer):
            self.meeting_duration_timer.cancel()
            try:
                time: int = await self.meeting_duration_timer
                self.meeting_duration = time
            except asyncio.CancelledError:
                pass
        print(self.meeting_duration)

        await utils.set_participant_count(
            access_code=self.access_code, count=self.participant_count
        )

        # Send end meeting message to host frontend
        await self._send_json(
            data={
                "type": MessageTypes.END_MEETING,
                "url": f"{reverse(viewname='post-meeting-host', kwargs={'meeting_id': str(self.meeting_id)})}",
            }
        )

        # Trigger end meeting for all participants
        await self.channel_layer.group_send(
            group=f"{GroupPrefixes.PARTICIPANT}{self.access_code}",
            message={"type": MessageTypes.END_MEETING},
        )
        await self._close_with_log(message="Meeting successfully closed")

    async def next_question(self, event: dict[str, Any]) -> None:
        # Send the next question to all participants
        question: str = event.get("question", "")
        if question:
            await self.channel_layer.group_send(
                group=f"{GroupPrefixes.PARTICIPANT}{self.access_code}",
                message={"type": MessageTypes.NEXT_QUESTION, "question": question},
            )

    async def answer_submitted(self, event: dict[str, Any]) -> None:
        # User submitted an answer
        await self._send_json(data={"type": MessageTypes.ANSWER_SUBMITTED})

    async def participant_joined(self, event: dict[str, Any]) -> None:
        participant_channel = event.get("participant_channel")
        participant_name = event.get("participant_name")
        if participant_channel and participant_name:
            self.participant_count += 1
            await self._send_json(
                data={
                    "type": MessageTypes.PARTICIPANT_JOINED,
                    "participant": {
                        "name": participant_name,
                        "status": "Connected",
                    },
                }
            )

    async def participant_left(self, event: dict[str, Any]) -> None:
        participant_name = event.get("name")
        if participant_name:
            await self._send_json(
                data={"type": MessageTypes.PARTICIPANT_LEFT, "name": participant_name}
            )


"""
PARTICIPANT CONSUMER
"""


class ParticipantMeetingConsumer(BaseMeetingConsumer):
    async def connect(self) -> None:
        # 1: Ensure URL Route is accessible
        url_route: dict[str, Any] | None = self._get_url_route()
        if not url_route:
            await self._close_with_log(
                code=CloseCodes.NO_URL_ROUTE.code,
                message=CloseCodes.NO_URL_ROUTE.message,
            )
            return

        # 2: Accept the connection
        await self.accept()
        self.access_code: str = url_route["kwargs"]["access_code"]
        # IMPORTANT -> Immediately close the connection IF the meeting has already started
        if await cache.aget(key=f"{GroupPrefixes.MEETING_LOCKED}{self.access_code}"):
            await self.close(code=4401, reason="meeting_locked")
            return
        # 3: Define base model attributes
        self.group_name: str = f"{GroupPrefixes.PARTICIPANT}{self.access_code}"
        self.host_group_name: str = f"{GroupPrefixes.HOST}{self.access_code}"

    async def disconnect(self, code: int) -> None:
        # Notify the host that a participant left
        if hasattr(self, "host_group_name") and self.host_group_name:
            await self.channel_layer.group_send(
                group=self.host_group_name,
                message={
                    "type": MessageTypes.PARTICIPANT_LEFT,
                    "name": self.name,
                },
            )

        # Remove self from participant group
        if hasattr(self, "group_name") and self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        if not text_data:
            return
        try:
            text_data_json: dict[str, Any] = json.loads(text_data)
            message_type: str = text_data_json["type"]
            match message_type:
                case MessageTypes.PARTICIPANT_JOINED:
                    # This match is received immediately after `connect` is done
                    await self.participant_joined(event=text_data_json)
                case MessageTypes.SUBMIT_ANSWER:
                    await self.submit_answer(event=text_data_json)
        except json.JSONDecodeError:
            pass  # For now

    # HANDLER METHODS FOR PARTICIPANT CONSUMER
    async def start_meeting(self, event: dict[str, Any]) -> None:
        question = event.get("question", "")
        await self._send_json(
            data={"type": MessageTypes.START_MEETING, "question": question}
        )

    async def end_meeting(self, event: dict[str, Any]) -> None:
        # `Url` is used to redirect user window on front end
        await self._send_json(
            data={"type": MessageTypes.END_MEETING, "url": f"{reverse('post-meeting')}"}
        )
        await self.close()

    async def next_question(self, event: dict[str, Any]) -> None:
        # Send the next question to the front end
        question = event.get("question", "")
        await self._send_json(
            data={"type": MessageTypes.NEXT_QUESTION, "question": question}
        )

    async def participant_joined(self, event: dict[str, Any]) -> None:
        name: str | None = event.get("name", None)
        if not name:
            # Should Never Happen but good check
            await self._close_with_log(message="Participant Name Not Found")
            return
        user_names: list[str] | None = await cache.aget(
            key=utils.get_username_cache_key(self.access_code)
        )
        if user_names is None:
            await self._close_with_log(message="Joined before Host", code=4004)
            return
        # Prevent name duplicates
        name_count: int = sum(n == name or n.startswith(f"{name}(") for n in user_names)
        if name_count > 0:
            self.name: str = f"{name}({name_count})"
            # Add name number on front end
            await self._send_json(
                data={"type": MessageTypes.UPDATE_NAME, "name": self.name}
            )
        else:
            self.name: str = name
        # Update the usernames list
        user_names.append(self.name)
        # Update the cached usernames list
        await cache.aset(
            key=utils.get_username_cache_key(self.access_code),
            value=user_names,
            timeout=3600,
        )
        # Add the Participant to the Participant Group Channel
        await self.channel_layer.group_add(
            group=self.group_name, channel=self.channel_name
        )
        # Let the host know that a participant joined
        await self.channel_layer.group_send(
            group=self.host_group_name,
            message={
                "type": MessageTypes.PARTICIPANT_JOINED,
                "participant_name": self.name,
                "participant_channel": self.channel_name,
            },
        )

    async def submit_answer(self, event: dict[str, Any]) -> None:
        # These return statements will later be updated to return useful info to frontend
        answer: str | None = event.get("answer", None)
        question_description: str | None = event.get("question", None)
        if not answer or not question_description:
            await self._send_json(data={"type": MessageTypes.SUBMIT_ERROR})
            return  # Question won't be counted
        meeting_obj: Meeting | None = await utils.get_meeting_by_access_code(
            access_code=self.access_code
        )
        if not meeting_obj:
            await self._send_json(data={"type": MessageTypes.SUBMIT_ERROR})
            return  # SHOULD NEVER HAPPEN
        question_obj: Question | None = await utils.get_question(
            description=question_description, meeting=meeting_obj
        )
        if not question_obj:
            await self._send_json(data={"type": MessageTypes.SUBMIT_ERROR})
            return  # SHOULD NEVER HAPPEN
        response_obj: Response | None = await utils.create_response_model(
            meeting=meeting_obj, question=question_obj, response_text=answer
        )
        if not response_obj:
            await self._send_json(data={"type": MessageTypes.INVALID_ANSWER})
            return  # User submitted invalid info
        await response_obj.asave()
        # Let the host know a valid answer has been submitted
        await self.channel_layer.group_send(
            group=f"{GroupPrefixes.HOST}{self.access_code}",
            message={"type": MessageTypes.ANSWER_SUBMITTED},
        )
