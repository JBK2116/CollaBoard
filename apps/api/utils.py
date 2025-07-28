import uuid
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from apps.director.models import Meeting, Question
from apps.meeting.models import Response

"""
Summary dict structure:
{
    "meeting_title": str,          # Meeting title
    "date": str,                   # Meeting date (formatted)
    "time_created": str,           # Meeting time (formatted)
    "author": str,                 # Meeting director's full name
    "questions_analysis": [        # List of question analysis dicts
        {
            "question": str,       # Original question text
            "summary": str,        # 3-sentence response synthesis
            "response_count": int  # Number of responses
        }
    ],
    "key_takeaways": [str]         # List of actionable takeaway strings
}
"""


def format_meeting_time(time: datetime) -> dict[str, str]:
    """
    Formats the provided datetime object into two
    string fields.

    The first field being a
    created at date in the format `DD/MM/YYYY`.

    The second field being a time created field
    in the format `HH/MM`

    Returns:
        - dict[str, Any]: The formatted times dictionary

    Example Return:
    ```
    {
        "created_at": "February 11 2025",
        "time_created": "14:30"
    }
    ```
    """
    # NOTE: local_timezone is a timezone converter to convert a datetimefield into the provided key timezone
    # NOTE: astimezone accepts a timezone converter and converts the datetime object to that timezone
    local_timezone: ZoneInfo = ZoneInfo(key="America/Toronto")
    local_time: datetime = time.astimezone(local_timezone)
    time_dictionary: dict[str, str] = {
        "created_at": local_time.strftime("%d %B %Y"),
        "time_created": local_time.strftime("%H:%M"),
    }
    return time_dictionary


def get_meeting_data(meeting_id: str) -> dict[str, Any] | None:
    """
    Fetches a meeting object from the database
    using the provided meeting_id. Then extracts
    all of its related questions and responses.

    `Utilizes prefetch_related to additionally retrieve
    all linked question and response objects to the meeting`

    Returns:
        - dict [str, Any] | None: The meeting info dictionary or None if an error occurs

    Example Return:
        ```
        {
            "meeting": meeting (Meeting)
            "questions": [Question]
            "responses": [Response]
        }
        ```
    """
    try:
        meeting: Meeting = Meeting.objects.prefetch_related(
            "questions", "response_set"
        ).get(id=uuid.UUID(meeting_id))
        # NOTE: The ignore comments are because the IDE does not recognize the attributes.
        questions: list[Question] = meeting.questions.all()  # type: ignore
        responses: list[Response] = meeting.response_set.all()  # type: ignore
        return {"meeting": meeting, "questions": questions, "responses": responses}
    except (ValueError, Meeting.DoesNotExist):
        return None


def format_question_responses(
    questions: list[Question], responses: list[Response]
) -> dict[str, Any]:
    """
    Iterates over both the questions list and the responses list.
    Generates a dictionary of question response combinations
    with the question being the key and a list of it's
    corresponding responses being the value

    Returns:
        - dict[str, Any]: A dictionary with questions as keys and their responses as values in a list

    Example Return:
        ```
        {
            "question_one_desc": list[response_text]
            "question_two_desc" : list[response_text]
        }
        ```
    """
    # NOTE: This algorithm will be optimized in the future
    all_questions_descriptions: list[str] = [
        f"Question {question.position}: {question.description}"
        for question in questions
    ]
    all_responses_descriptions: list[list[str]] = []
    for question in questions:
        response_descriptions: list[str] = [
            r.response_text for r in responses if r.question == question
        ]
        if not response_descriptions:
            response_descriptions.append("No responses received for this question")
        all_responses_descriptions.append(response_descriptions)

    qa_dictionary: dict[str, Any] = {
        k: v for (k, v) in zip(all_questions_descriptions, all_responses_descriptions)
    }
    return qa_dictionary
