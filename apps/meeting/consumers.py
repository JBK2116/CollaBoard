import json
import uuid
from typing import Any, cast
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.sessions.models import Session

from apps.base.models import CustomUser
from apps.director.models import Meeting, Question

"""
# These are the prefixes, access code will be added on top of both
like f"{host_group}{access_code}"
"""
host_group = "meeting_host_"
participant_group = "meeting_"


class HostMeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        url_route: dict[str, Any] | None = self.scope.get("url_route")
        if not url_route:
            print("No URL route - closing")
            await self.close()
            return

        self.meeting_id: uuid.UUID = url_route["kwargs"]["meeting_id"]

        # Get session ID from query parameters
        query_string = self.scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        session_id = query_params.get("session", [None])[0]

        if not session_id:
            print("No session ID provided - closing")
            await self.close()
            return

        # Get user from session
        user = await self.get_user_from_session(session_id)

        if user is None or not user.is_authenticated:
            print("Auth Failed: Closing the connection!")
            await self.close()
            return

        # User is guaranteed to be authenticated now
        await self.accept()
        user = cast(CustomUser, user)

        # Get all meeting questions
        meeting_questions: list[Question] | None = await database_sync_to_async(
            get_meeting_questions
        )(meeting_id=self.meeting_id)

        if not meeting_questions:
            # Should never happen, but good to check for it
            await self.close(code=4004)
            return
        access_code = await database_sync_to_async(get_access_code)(
            meeting_id=self.meeting_id
        )

        self.group_name: str = f"{host_group}{access_code}"
        await self.channel_layer.group_add(
            group=self.group_name, channel=self.channel_name
        )

        questions: list[str] = [q.description for q in meeting_questions]
        await self.send(
            text_data=json.dumps(
                {
                    "type": "questions",
                    "questions": questions,
                    "access_code": access_code,
                }
            )
        )

    @database_sync_to_async
    def get_user_from_session(self, session_key: str) -> CustomUser | None:
        """Get user from session key"""
        try:
            session = Session.objects.get(session_key=session_key)
            uid = session.get_decoded().get("_auth_user_id")
            if uid:
                return CustomUser.objects.get(pk=uid)
        except (Session.DoesNotExist, CustomUser.DoesNotExist):
            return None
        return None

    async def disconnect(self, code: int) -> None:
        pass

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        if not text_data:
            return
        text_data_json: dict[str, Any] = json.loads(text_data)
        message_type: str = text_data_json["type"]
        if (
            message_type == "start_meeting"
        ):  # Hard-Coded values will be refactored into an ENUM later
            await self.start_meeting(event=text_data_json)
        elif message_type == "next_question":
            await self.next_question(event=text_data_json)

    async def participant_joined(self, event: dict[str, Any]) -> None:
        participant_channel = event["participant_channel"]
        await self.send(
            text_data=json.dumps(
                {
                    "type": "participant_joined",
                    "participant": {
                        "id": participant_channel,
                        "name": "Anon",
                        "status": "Waiting",
                    },
                    "channel": participant_channel,
                }
            )
        )

    async def start_meeting(self, event: dict[str, Any]) -> None:
        access_code: str = event["access_code"]
        first_question: str = event["question"]
        first_question = first_question.strip()
        await self.channel_layer.group_send(
            group=f"{participant_group}{access_code}",
            message={"type": "meeting_started", "question": first_question},
        )

    async def next_question(self, event: dict[str, Any]) -> None:
        access_code: str = event["access_code"]
        question: str = event["question"]
        question = question.strip()
        await self.channel_layer.group_send(
            group=f"{participant_group}{access_code}",
            message={"type": "new_question", "question": question},
        )


class ParticipantMeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        url_route: dict[str, Any] | None = self.scope.get("url_route")
        if not url_route:
            print("No URL route - closing")
            await self.close()
            return
        access_code: str = url_route["kwargs"]["access_code"]
        self.group_name: str = f"{participant_group}{access_code}"
        self.host_group_name: str = f"{host_group}{access_code}"
        # Define's the group name: Will be something like meeting(_host)_12345678
        await self.channel_layer.group_add(
            group=self.group_name, channel=self.channel_name
        )
        # Add the user's channel to the group
        await self.accept()
        await self.channel_layer.group_send(
            group=self.host_group_name,
            message={
                "type": "participant_joined",
                "participant_channel": self.channel_name,
            },
        )

    async def disconnect(self, code: int) -> None:
        pass

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        if text_data:
            text_data_json = json.loads(text_data)
            message = text_data_json["message"]

            await self.send(text_data=json.dumps({"message": message}))

    async def meeting_started(self, event: dict[str, Any]) -> None:
        await self.send(
            text_data=json.dumps(
                {"type": "meeting_started", "question": event["question"]}
            )
        )
    async def new_question(self, event: dict[str, Any]) -> None:
        await self.send(
            text_data=json.dumps({
                "type": "new_question",
                "question": event["question"]
            })
        )


"""
Below are database queries used
during the connections
"""


def get_meeting_questions(meeting_id: uuid.UUID) -> list[Question] | None:
    try:
        meeting: Meeting = Meeting.objects.prefetch_related("questions").get(
            id=meeting_id
        )
        questions: list[Question] = list(meeting.questions.all())  # type: ignore -> Mypy is Tweaking
        return questions
    except Meeting.DoesNotExist:
        return None


def get_access_code(meeting_id: uuid.UUID) -> str | None:
    try:
        meeting: Meeting = Meeting.objects.get(id=meeting_id)
        access_code = meeting.access_code
        return access_code
    except Meeting.DoesNotExist:
        return None
