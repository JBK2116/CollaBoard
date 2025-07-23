"""
This module stores utility functions
used by the websocket consumers in `consumers.py`.
The types of functions include "database query functions",
"authentication functions", and more.
"""

import uuid
from typing import NamedTuple

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError

from apps.base.models import CustomUser
from apps.director.models import Meeting, Question
from apps.meeting.models import Response


class MeetingData(NamedTuple):
    """Container for meeting with associated data"""
    meeting: Meeting
    questions: list[Question]
    access_code: str


@database_sync_to_async
def get_meeting_with_questions(meeting_id: uuid.UUID) -> MeetingData | None:
    """
    Retrieves meeting with all associated questions and access code in a single query.
    
    Args:
        meeting_id (uuid.UUID): The UUID of the meeting.
        
    Returns:
        MeetingData | None: Meeting data container if found; otherwise, None.
    """
    try:
        meeting = Meeting.objects.prefetch_related("questions").get(id=meeting_id)
        questions = list(meeting.questions.all()) # type: ignore
        return MeetingData(
            meeting=meeting,
            questions=questions,
            access_code=meeting.access_code
        )
    except Meeting.DoesNotExist:
        return None


@database_sync_to_async
def get_meeting_questions(meeting_id: uuid.UUID) -> list[Question] | None:
    """
    Retrieves all questions associated with the meeting identified by the given `meeting_id`.

    Args:
        meeting_id (uuid.UUID): The UUID of the meeting.

    Returns:
        list[Question] | None: A list of Question objects if the meeting exists; otherwise, None.
    """
    try:
        meeting = Meeting.objects.prefetch_related("questions").get(id=meeting_id)
        questions: list[Question] = list(meeting.questions.all())  # type: ignore
        return questions
    except Meeting.DoesNotExist:
        return None


@database_sync_to_async
def get_access_code(meeting_id: uuid.UUID) -> str | None:
    """
    Retrieves the access code for the meeting with the given `meeting_id`.

    Args:
        meeting_id (uuid.UUID): The UUID of the meeting.

    Returns:
        str | None: The access code if the meeting exists; otherwise, None.
    """
    try:
        meeting = Meeting.objects.only('access_code').get(id=meeting_id)
        return meeting.access_code
    except Meeting.DoesNotExist:
        return None


@database_sync_to_async
def get_meeting_by_access_code(access_code: str) -> Meeting | None:
    """
    Retrieves the meeting instance corresponding to the given access code.

    Args:
        access_code (str): The access code of the meeting.

    Returns:
        - Meeting | None: The Meeting object if found; otherwise, None.
    """
    try:
        return Meeting.objects.get(access_code=access_code)
    except Meeting.DoesNotExist:
        return None


@database_sync_to_async
def get_question(description: str, meeting: Meeting) -> Question | None:
    """
    Retrieves the question instance of a specific meeting corresponding to the given description.

    Args:
        description (str): The description of the question.
        meeting (Meeting): The meeting instance.

    Returns:
        Question | None: The Question object if found; otherwise, None.
    """
    try:
        return Question.objects.get(description=description, meeting=meeting)
    except Question.DoesNotExist:
        return None


@database_sync_to_async
def get_question_by_description_and_access_code(description: str, access_code: str) -> Question | None:
    """
    Retrieves question by description and meeting access code in a single query.
    More efficient than getting meeting first, then question.
    
    Args:
        description (str): The description of the question.
        access_code (str): The access code of the meeting.
        
    Returns:
        Question | None: The Question object if found; otherwise, None.
    """
    try:
        return Question.objects.select_related('meeting').get(
            description=description, 
            meeting__access_code=access_code
        )
    except Question.DoesNotExist:
        return None


async def create_response_model(
    meeting: Meeting, question: Question, response_text: str
) -> Response | None:
    """
    Creates a response model and validates it.
    
    Args:
        meeting (Meeting): The meeting instance.
        question (Question): The question instance.
        response_text (str): The response text.
        
    Returns:
        Response | None: Valid Response object or None if validation fails.
    """
    new_response_obj = Response(
        meeting=meeting, 
        question=question, 
        response_text=response_text
    )
    try:
        await sync_to_async(new_response_obj.full_clean)()
        return new_response_obj
    except ValidationError:
        return None


def get_username_cache_key(access_code: str) -> str:
    """
    Generates cache key for storing participant usernames.
    
    Args:
        access_code (str): The meeting access code.
        
    Returns:
        str: Cache key for usernames.
    """
    return f"meeting:{access_code}:names"


@database_sync_to_async
def get_user_from_session(session_key: str) -> CustomUser | None:
    """
    Retrieves the authenticated user associated with the given session key.

    Args:
        session_key (str): The session key from the user's cookies.

    Returns:
        CustomUser | None: The user object if found and valid; otherwise, None.
    """
    try:
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get("_auth_user_id")
        if uid:
            return CustomUser.objects.get(pk=uid)
    except (Session.DoesNotExist, CustomUser.DoesNotExist):
        pass
    return None