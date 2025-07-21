import json
import uuid
from typing import Any

from channels.db import database_sync_to_async
from django.core.cache import cache
from django.urls import reverse

from apps.director.models import Question
from apps.meeting import utils
from apps.meeting.base import BaseMeetingConsumer
from apps.meeting.constants import CloseCodes, GroupPrefixes, MessageTypes

"""
HOST CONSUMER HERE
"""


class HostMeetingConsumer(BaseMeetingConsumer):
    async def connect(self) -> None:
        url_route: dict[str, Any] | None = self._get_url_route()
        if not url_route:
            await self._close_with_log(
                code=CloseCodes.NO_URL_ROUTE.code,
                message=CloseCodes.NO_URL_ROUTE.message,
            )
            return

        self.meeting_id: uuid.UUID = url_route["kwargs"]["meeting_id"]

        # Get session ID from query parameters
        session_id: str | None = self._get_session_id_from_query()
        if not session_id:
            await self._close_with_log(
                code=CloseCodes.NO_SESSION.code, message=CloseCodes.NO_SESSION.message
            )
            return

        # Get user from session
        user = await utils.get_user_from_session(session_id)
        if user is None or not user.is_authenticated:
            await self._close_with_log(
                code=CloseCodes.AUTH_FAILED.code, message=CloseCodes.AUTH_FAILED.message
            )
            return

        # Get meeting access code
        access_code: str | None = await database_sync_to_async(utils.get_access_code)(
            meeting_id=self.meeting_id
        )
        if not access_code:
            await self._close_with_log(
                code=CloseCodes.NO_ACCESS_CODE.code,
                message=CloseCodes.NO_ACCESS_CODE.message,
            )
            return
        self.access_code = access_code

        # Get all meeting questions
        meeting_questions: list[Question] | None = await database_sync_to_async(
            utils.get_meeting_questions
        )(meeting_id=self.meeting_id)
        if not meeting_questions:
            await self._close_with_log(
                code=CloseCodes.NO_QUESTIONS.code,
                message=CloseCodes.NO_QUESTIONS.message,
            )
            return

        # Accept connection before any group operations
        await self.accept()
        await cache.aset(
            key=f"{GroupPrefixes.MEETING_LOCKED}{self.access_code}",
            value=False,
            timeout=3600,
        )
        # Add The Host to their dedicated channel group
        self.group_name: str = f"{GroupPrefixes.HOST}{self.access_code}"
        await self.channel_layer.group_add(
            group=self.group_name, channel=self.channel_name
        )
        self.meeting_locked = False

        # Get all meeting question descriptions
        questions: list[str] = [q.description for q in meeting_questions]

        # Send all questions to the host frontend
        await self._send_json(
            data={
                "type": MessageTypes.START_MEETING,
                "questions": questions,
                "access_code": self.access_code,
            }
        )

    async def disconnect(self, code: int) -> None:
        # Remove Host from group if access_code exists
        if hasattr(self, "access_code") and self.access_code:
            await self.channel_layer.group_discard(
                f"{GroupPrefixes.HOST}{self.access_code}", self.channel_name
            )
            await self.channel_layer.group_send(
                group=f"{GroupPrefixes.PARTICIPANT}{self.access_code}",
                message={"type": MessageTypes.END_MEETING},
            )
            await cache.adelete(key=f"{GroupPrefixes.MEETING_LOCKED}{self.access_code}")

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        if not text_data:
            return

        try:
            text_data_json: dict[str, Any] = json.loads(text_data)
            message_type: str = text_data_json["type"]

            if message_type == MessageTypes.START_MEETING:
                await self.start_meeting(event=text_data_json)
            elif message_type == MessageTypes.NEXT_QUESTION:
                await self.next_question(event=text_data_json)
            elif message_type == MessageTypes.END_MEETING:
                await self.end_meeting(event=text_data_json)
        except json.JSONDecodeError:
            # Ignore invalid JSON
            pass

    # HANDLER METHODS FOR HOST CONSUMER

    async def start_meeting(self, event: dict[str, Any]) -> None:
        await cache.aset(
            key=f"{GroupPrefixes.MEETING_LOCKED}{self.access_code}", value=True
        )
        question: str = event.get("question", "").strip()
        if question:
            await self.channel_layer.group_send(
                group=f"{GroupPrefixes.PARTICIPANT}{self.access_code}",
                message={"type": MessageTypes.START_MEETING, "question": question},
            )

    async def next_question(self, event: dict[str, Any]) -> None:
        question: str = event.get("question", "").strip()
        if question:
            await self.channel_layer.group_send(
                group=f"{GroupPrefixes.PARTICIPANT}{self.access_code}",
                message={"type": MessageTypes.NEXT_QUESTION, "question": question},
            )

    async def end_meeting(self, event: dict[str, Any]) -> None:
        await self.channel_layer.group_send(
            group=f"{GroupPrefixes.PARTICIPANT}{self.access_code}",
            message={"type": MessageTypes.END_MEETING},
        )
        await self.close()

    async def participant_joined(self, event: dict[str, Any]) -> None:
        participant_channel = event.get("participant_channel")
        if participant_channel:
            await self._send_json(
                data={
                    "type": MessageTypes.PARTICIPANT_JOINED,
                    "participant": {
                        "id": participant_channel,
                        "name": "Anon",
                        "status": "Connected",
                    },
                    "channel": participant_channel,
                }
            )

    async def participant_left(self, event: dict[str, Any]) -> None:
        participant_channel = event.get("id")
        if participant_channel:
            await self._send_json(
                data={"type": MessageTypes.PARTICIPANT_LEFT, "id": participant_channel}
            )


"""
PARTICIPANT CONSUMER
"""


class ParticipantMeetingConsumer(BaseMeetingConsumer):
    async def connect(self) -> None:
        url_route: dict[str, Any] | None = self._get_url_route()
        if not url_route:
            await self._close_with_log(
                code=CloseCodes.NO_URL_ROUTE.code,
                message=CloseCodes.NO_URL_ROUTE.message,
            )
            return
        # Accept the connection
        await self.accept()
        self.access_code: str = url_route["kwargs"]["access_code"]
        # Immediately close it IF the meeting has already started
        if await cache.aget(key=f"{GroupPrefixes.MEETING_LOCKED}{self.access_code}"):
            await self.close(code=4401, reason=f"meeting_locked")
            return
        # Define model attributes
        self.group_name: str = f"{GroupPrefixes.PARTICIPANT}{self.access_code}"
        self.host_group_name: str = f"{GroupPrefixes.HOST}{self.access_code}"

        # Add the Participant to the Participant Group Channel
        await self.channel_layer.group_add(
            group=self.group_name, channel=self.channel_name
        )

        # Let the Host Consumer know that a new Participant has joined
        await self.channel_layer.group_send(
            group=self.host_group_name,
            message={
                "type": MessageTypes.PARTICIPANT_JOINED,
                "participant_channel": self.channel_name,
            },
        )

    async def disconnect(self, code: int) -> None:
        # Notify host that participant left
        if hasattr(self, "host_group_name") and self.host_group_name:
            await self.channel_layer.group_send(
                group=self.host_group_name,
                message={
                    "type": MessageTypes.PARTICIPANT_LEFT,
                    "id": self.channel_name,
                },
            )

        # Remove from participant group
        if hasattr(self, "group_name") and self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        if not text_data:
            return

        # try:
        #     text_data_json: dict[str, Any] = json.loads(text_data)
        #     message_type: str = text_data_json.get("type")

        #     # Handle any participant messages here if needed in the future
        #     # For now, participants only receive messages, don't send meaningful ones
        #     pass
        # except json.JSONDecodeError:
        #     # Ignore invalid JSON
        #     pass

    # HANDLER METHODS FOR PARTICIPANT CONSUMER

    async def start_meeting(self, event: dict[str, Any]) -> None:
        question = event.get("question", "")
        await self._send_json(
            data={"type": MessageTypes.START_MEETING, "question": question}
        )

    async def next_question(self, event: dict[str, Any]) -> None:
        question = event.get("question", "")
        await self._send_json(
            data={"type": MessageTypes.NEXT_QUESTION, "question": question}
        )

    async def end_meeting(self, event: dict[str, Any]) -> None:
        await self._send_json(
            data={"type": MessageTypes.END_MEETING, "url": f"{reverse('post-meeting')}"}
        )
        await self.close()
