import json
import uuid
from typing import Any, cast

from channels.db import database_sync_to_async

from apps.base.models import CustomUser
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
            print("No URL route - closing")
            await self._close_with_log(
                code=CloseCodes.NO_URL_ROUTE.code,
                message=CloseCodes.NO_URL_ROUTE.message,
            )
            return

        self.meeting_id: uuid.UUID = url_route["kwargs"]["meeting_id"]

        # Get session ID from query parameters
        session_id: str | None = self._get_session_id_from_query()
        if not session_id:
            print("No session ID provided - closing")
            await self._close_with_log(
                code=CloseCodes.NO_SESSION.code, message=CloseCodes.NO_SESSION.message
            )
            return

        # Get user from session
        user = await utils.get_user_from_session(session_id)
        if user is None or not user.is_authenticated:
            print("Auth Failed: Closing the connection!")
            await self._close_with_log(
                code=CloseCodes.AUTH_FAILED.code, message=CloseCodes.AUTH_FAILED.message
            )
            return

        # User is guaranteed to be authenticated now
        await self.accept()
        user = cast(CustomUser, user)

        # Get all meeting questions
        meeting_questions: list[Question] | None = await database_sync_to_async(
            utils.get_meeting_questions
        )(meeting_id=self.meeting_id)
        if not meeting_questions:
            # Should never happen, but good to check for it
            await self._close_with_log(
                code=CloseCodes.NO_QUESTIONS.code,
                message=CloseCodes.NO_QUESTIONS.message,
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

        # Add The Host to their dedicated channel group
        self.group_name: str = f"{GroupPrefixes.HOST}{self.access_code}"
        await self.channel_layer.group_add(
            group=self.group_name, channel=self.channel_name
        )

        # Get all meeting question descriptions
        questions: list[str] = [q.description for q in meeting_questions]

        # Send all questions to the host (Questions used for entire meeting length)
        await self._send_json(
            data={
                "type": MessageTypes.START_MEETING,
                "questions": questions,
                "access_code": self.access_code,
            }
        )

    async def disconnect(self, code: int) -> None:
        # Remove Host from group then close websocket connection
        await self.channel_layer.group_discard(
            f"{GroupPrefixes.HOST}{self.access_code}", self.channel_name
        )
        await self._close_with_log(message=CloseCodes.SUCCESSFUL_CLOSE.message)

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        if not text_data:
            return
        text_data_json: dict[str, Any] = json.loads(text_data)
        message_type: str = text_data_json["type"]

        # Chose proper function to handle message type
        if message_type == MessageTypes.START_MEETING:
            print(text_data_json)
            await self.start_meeting(event=text_data_json)
        elif message_type == MessageTypes.NEXT_QUESTION:
            await self.next_question(event=text_data_json)
        elif message_type == MessageTypes.END_MEETING:
            await self.end_meeting(event=text_data_json)

    # BELOW ARE HANDLER METHODS FOR THIS HOST CONSUMER

    async def start_meeting(self, event: dict[str, Any]) -> None:
        access_code: str = event["access_code"]
        first_question: str = event["question"]
        first_question = first_question.strip()
        await self.channel_layer.group_send(
            group=f"{GroupPrefixes.PARTICIPANT}{access_code}",
            message={"type": MessageTypes.START_MEETING, "question": first_question},
        )

    async def next_question(self, event: dict[str, Any]) -> None:
        access_code: str = event["access_code"]
        question: str = event["question"]
        question = question.strip()
        await self.channel_layer.group_send(
            group=f"{GroupPrefixes.PARTICIPANT}{access_code}",
            message={"type": MessageTypes.NEXT_QUESTION, "question": question},
        )

    async def participant_joined(self, event: dict[str, Any]) -> None:
        participant_channel = event["participant_channel"]
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
        participant_channel = event["id"]
        await self._send_json(
            data={
                "type": MessageTypes.PARTICIPANT_LEFT,
                "id": participant_channel
            }
        )
    async def end_meeting(self, event: dict[str, Any]) -> None:
        await self.channel_layer.group_send(
            group=f"{GroupPrefixes.PARTICIPANT}{self.access_code}",
            message={"type": MessageTypes.END_MEETING}
        )
        await self.close()


"""
BELOW IS THE PARTICIPANT CONSUMER
"""


class ParticipantMeetingConsumer(BaseMeetingConsumer):
    async def connect(self) -> None:
        url_route: dict[str, Any] | None = self._get_url_route()
        if not url_route:
            print("No URL route - closing")
            await self._close_with_log(
                code=CloseCodes.NO_URL_ROUTE.code,
                message=CloseCodes.NO_URL_ROUTE.message,
            )
            return

        # Define model attributes
        self.access_code: str = url_route["kwargs"]["access_code"]
        self.group_name: str = f"{GroupPrefixes.PARTICIPANT}{self.access_code}"
        self.host_group_name: str = f"{GroupPrefixes.HOST}{self.access_code}"

        # Add the Participant to the Participant Group Channel
        await self.channel_layer.group_add(
            group=self.group_name, channel=self.channel_name
        )

        # Let the Host Consumer know that a new Participant has joined
        await self.accept()
        await self.channel_layer.group_send(
            group=self.host_group_name,
            message={
                "type": MessageTypes.PARTICIPANT_JOINED,
                "participant_channel": self.channel_name,
            },
        )

    async def disconnect(self, code: int) -> None:
        await self.channel_layer.group_send(
            group=self.host_group_name,
            message={"type": MessageTypes.PARTICIPANT_LEFT, "id": self.channel_name}
        )

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        if not text_data:
            return
        text_data_json: dict[str, Any] = json.loads(text_data)
        message_type: str = text_data_json["type"]

    # BELOW ARE HANDLER METHODS FOR THIS PARTCIPANT CONSUMER
    async def start_meeting(self, event: dict[str, Any]) -> None:
        await self._send_json(
            data={"type": MessageTypes.START_MEETING, "question": event["question"]}
        )
    
    async def end_meeting(self, event: dict[str, Any]) -> None:
        await self._send_json(
            data={"type": MessageTypes.END_MEETING}
        )

    async def next_question(self, event: dict[str, Any]) -> None:
        await self._send_json(
            data={"type": MessageTypes.NEXT_QUESTION, "question": event["question"]}
        )
