"""
Meeting WebSocket Utilities Module

This module provides utility functions for WebSocket consumers in `consumers.py`.
Includes database query functions, authentication helpers, cache utilities,
and meeting lifecycle management functions.

Functions are categorized as:
- Database query operations (async database access)
- Authentication and session management
- Meeting statistics and duration tracking
- Cache key generation and management
"""

import asyncio
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
    """
    Container for meeting data with associated questions and access code.

    Attributes:
        meeting: The Meeting model instance
        questions: List of associated Question instances
        access_code: The meeting's unique access code for participants
    """

    meeting: Meeting
    questions: list[Question]
    access_code: str


@database_sync_to_async
def get_meeting_with_questions(meeting_id: uuid.UUID) -> MeetingData | None:
    """
    Retrieves meeting with all associated questions and access code in a single optimized query.

    Uses prefetch_related to minimize database queries and improve performance.

    Args:
        meeting_id: The UUID identifier of the meeting

    Returns:
        MeetingData: Container with meeting, questions, and access code if found;
        OR `None: if meeting doesn't exist`

    Note:
        This is the preferred method for getting meeting data as it reduces
        database round trips compared to separate queries.
    """
    try:
        meeting_instance = Meeting.objects.prefetch_related("questions").get(
            id=meeting_id
        )
        associated_questions = list(meeting_instance.questions.all())  # type: ignore
        return MeetingData(
            meeting=meeting_instance,
            questions=associated_questions,
            access_code=meeting_instance.access_code,
        )
    except Meeting.DoesNotExist:
        return None


@database_sync_to_async
def get_meeting_questions(meeting_id: uuid.UUID) -> list[Question] | None:
    """
    Retrieves all questions associated with a specific meeting.

    Args:
        meeting_id: The UUID identifier of the meeting

    Returns:
        List of Question objects if meeting exists; None if meeting not found

    Note:
        Consider using get_meeting_with_questions() if you also need
        the meeting instance to reduce database queries.
    """
    try:
        meeting_instance = Meeting.objects.prefetch_related("questions").get(
            id=meeting_id
        )
        questions_list: list[Question] = list(meeting_instance.questions.all())  # type: ignore
        return questions_list
    except Meeting.DoesNotExist:
        return None


@database_sync_to_async
def get_access_code(meeting_id: uuid.UUID) -> str | None:
    """
    Retrieves the access code for a specific meeting.

    Uses only() to optimize query by fetching only the access_code field.

    Args:
        meeting_id: The UUID identifier of the meeting

    Returns:
        The meeting's access code string if found; None if meeting doesn't exist
    """
    try:
        meeting_instance = Meeting.objects.only("access_code").get(id=meeting_id)
        return meeting_instance.access_code
    except Meeting.DoesNotExist:
        return None


@database_sync_to_async
def get_meeting_by_access_code(access_code: str) -> Meeting | None:
    """
    Retrieves meeting instance using its unique access code.

    Args:
        access_code: The unique access code for the meeting

    Returns:
        Meeting instance if found; None if no meeting has this access code

    Note:
        Access codes should be unique across all meetings in the system.
    """
    try:
        return Meeting.objects.get(access_code=access_code)
    except Meeting.DoesNotExist:
        return None


@database_sync_to_async
def get_question(
    question_description: str, meeting_instance: Meeting
) -> Question | None:
    """
    Retrieves a specific question within a meeting by its description.

    Args:
        question_description: The text description of the question
        meeting_instance: The Meeting instance to search within

    Returns:
        Question instance if found; None if question doesn't exist in this meeting

    Note:
        Question descriptions should be unique within a single meeting.
    """
    try:
        return Question.objects.get(
            description=question_description, meeting=meeting_instance
        )
    except Question.DoesNotExist:
        return None


@database_sync_to_async
def get_question_by_description_and_access_code(
    question_description: str, meeting_access_code: str
) -> Question | None:
    """
    Retrieves question by description and meeting access code in a single optimized query.

    More efficient than getting meeting first, then question separately.
    Uses select_related to fetch meeting data in the same query.

    Args:
        question_description: The text description of the question
        meeting_access_code: The unique access code of the meeting

    Returns:
        Question instance with related meeting data if found; None otherwise

    Performance:
        This method is preferred when you have access_code instead of meeting_id
        as it reduces database queries compared to separate lookups.
    """
    try:
        return Question.objects.select_related("meeting").get(
            description=question_description, meeting__access_code=meeting_access_code
        )
    except Question.DoesNotExist:
        return None


async def set_participant_count(
    meeting_access_code: str, participant_count: int
) -> bool:
    """
    Updates the participant count field for a meeting.

    Validates count is within acceptable range before updating.

    Args:
        meeting_access_code: The unique access code of the meeting
        participant_count: The number of participants to set (1-1000)

    Returns:
        True if update was successful; False if meeting not found or count invalid

    Validation:
        - Participant count must be between 1 and 1000 inclusive
        - Meeting must exist in database
    """
    meeting_instance: Meeting | None = await get_meeting_by_access_code(
        access_code=meeting_access_code
    )
    if not meeting_instance:
        # ! This should never happen during normal meeting flow
        return False

    # NOTE: Validate participant count is within reasonable bounds
    if 0 < participant_count <= 1000:
        meeting_instance.participants = participant_count
        await database_sync_to_async(meeting_instance.save)()
        return True
    else:
        # ! Invalid participant count - consider logging this
        return False


async def set_meeting_duration_seconds_field(
    meeting_access_code: str, duration_seconds: int
) -> bool:
    """
    Updates the actual meeting duration in seconds.

    This records how long the meeting actually lasted, not the allocated time.

    Args:
        meeting_access_code: The unique access code of the meeting
        duration_seconds: Actual meeting duration in seconds (0-3600)

    Returns:
        True if update was successful; False if meeting not found or duration invalid

    Validation:
        - Duration must be between 0 and 3600 seconds (1 hour max)
        - Meeting must exist in database
    """
    meeting_instance: Meeting | None = await get_meeting_by_access_code(
        access_code=meeting_access_code
    )
    if not meeting_instance:
        # ! This should never happen during normal meeting flow
        return False

    # NOTE: Validate duration is within acceptable range (max 1 hour)
    if 0 <= duration_seconds <= 3600:
        meeting_instance.duration_in_seconds = duration_seconds
        await database_sync_to_async(meeting_instance.save)()
        return True
    else:
        # ! Invalid duration - consider logging this anomaly
        return False


async def set_total_questions_asked(
    meeting_access_code: str, questions_presented_count: int
) -> bool:
    """
    Updates the total number of questions presented during the meeting.

    Args:
        meeting_access_code: The unique access code of the meeting
        questions_presented_count: Number of questions actually presented (0-20)

    Returns:
        True if update was successful; False if meeting not found or count invalid

    Validation:
        - Question count must be between 0 and 20 inclusive
        - Meeting must exist in database
    """
    meeting_instance: Meeting | None = await get_meeting_by_access_code(
        access_code=meeting_access_code
    )
    if not meeting_instance:
        # ! This should never happen during normal meeting flow
        return False

    # NOTE: Validate question count is within system limits
    if 0 <= questions_presented_count <= 20:
        meeting_instance.total_questions_asked = questions_presented_count
        await database_sync_to_async(meeting_instance.save)()
        return True
    else:
        # ! Invalid question count - system allows max 20 questions
        return False


async def create_response_model(
    meeting_instance: Meeting,
    question_instance: Question,
    participant_response_text: str,
) -> Response | None:
    """
    Creates and validates a new Response model instance.

    Performs full model validation before returning the instance.
    The response is not saved to database - caller must save it.

    Args:
        meeting_instance: The Meeting this response belongs to
        question_instance: The Question being answered
        participant_response_text: The participant's answer text

    Returns:
        Valid Response instance ready for saving; None if validation fails

    Validation:
        Uses Django's full_clean() to validate all model constraints
        including custom validators, field constraints, and business rules.
    """
    new_response_instance = Response(
        meeting=meeting_instance,
        question=question_instance,
        response_text=participant_response_text,
    )

    try:
        # NOTE: Validate response according to model constraints
        await sync_to_async(new_response_instance.full_clean)()
        return new_response_instance
    except ValidationError:
        # NOTE: Response validation failed (e.g., text too long, invalid content)
        return None


def get_username_cache_key(meeting_access_code: str) -> str:
    """
    Generates standardized cache key for storing participant usernames.

    Args:
        meeting_access_code: The unique access code of the meeting

    Returns:
        Formatted cache key string for username storage

    Format:
        "meeting:{access_code}:names"

    Usage:
        Used to track participant usernames in Redis/cache to prevent
        duplicates and maintain participant lists during meeting sessions.
    """
    return f"meeting:{meeting_access_code}:names"


@database_sync_to_async
def get_user_from_session(session_key: str) -> CustomUser | None:
    """
    Retrieves authenticated user from Django session key.

    Used for WebSocket authentication where traditional request.user
    is not available.

    Args:
        session_key: The session key from user's cookies/query params

    Returns:
        CustomUser instance if session is valid and user exists; None otherwise

    Security:
        - Validates session exists and is not expired
        - Ensures user account still exists and is active
        - Returns None for any authentication failure

    ! SECURITY WARNING: In production, session keys should not be passed
    via URL parameters. Use secure headers or WebSocket subprotocols instead.
    """
    try:
        # NOTE: Retrieve session from Django's session store
        session_instance = Session.objects.get(session_key=session_key)

        # NOTE: Decode session data to extract user ID
        decoded_session_data = session_instance.get_decoded()
        user_id = decoded_session_data.get("_auth_user_id")

        if user_id:
            return CustomUser.objects.get(pk=user_id)

    except (Session.DoesNotExist, CustomUser.DoesNotExist):
        # NOTE: Session expired, invalid, or user no longer exists
        pass

    return None


async def meeting_duration_counter() -> int:
    """
    Tracks meeting elapsed time in seconds with cancellation support.

    This is a background task that counts seconds until cancelled.
    Used to track actual meeting duration regardless of allocated time.

    Returns:
        - Total elapsed seconds when task is cancelled

    ! CRITICAL: This task MUST be manually cancelled to prevent infinite loop.
    The task runs indefinitely until cancelled via asyncio.CancelledError.

    Usage:
        ```python
        duration_task = asyncio.create_task(meeting_duration_counter())
        # ... meeting activities ...
        duration_task.cancel()
        try:
            actual_duration = await duration_task
        except asyncio.CancelledError:
            # Task was cancelled as expected
            pass
        ```
    """
    elapsed_seconds_counter: int = 1

    try:
        while True:
            await asyncio.sleep(1)
            elapsed_seconds_counter += 1
    except asyncio.CancelledError:
        # NOTE: Task cancelled - return elapsed time
        return elapsed_seconds_counter
