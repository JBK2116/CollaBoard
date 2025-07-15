import json
import uuid
from typing import Any, cast
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session

from apps.base.models import CustomUser
from apps.director.models import Meeting, Question


class HostMeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
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

        questions: list[str] = [q.description for q in meeting_questions]
        await self.send(
            text_data=json.dumps({"type": "questions", "questions": questions})
        )

    @database_sync_to_async
    def get_user_from_session(self, session_key):
        """Get user from session key"""
        try:
            session = Session.objects.get(session_key=session_key)
            uid = session.get_decoded().get("_auth_user_id")
            if uid:
                user = get_user_model()
                return CustomUser.objects.get(pk=uid)
        except (Session.DoesNotExist, CustomUser.DoesNotExist):
            return None
        return None

    async def disconnect(self, code: int) -> None:
        pass

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        if text_data:
            text_data_json = json.loads(text_data)
            message = text_data_json["message"]

            await self.send(text_data=json.dumps({"message": message}))


class ParticipantMeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, code: int) -> None:
        pass

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        if text_data:
            text_data_json = json.loads(text_data)
            message = text_data_json["message"]

            await self.send(text_data=json.dumps({"message": message}))


"""
Below are database queries used
during the connections
"""


def get_meeting_questions(meeting_id: uuid.UUID) -> list[Question] | None:
    try:
        meeting: Meeting = Meeting.objects.prefetch_related("questions").get(
            id=meeting_id
        )
        questions: list[Question] = list(meeting.questions.all())  # type: ignore -> MYPY is tripping
        return questions
    except Meeting.DoesNotExist:
        return None
