import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from apps.director.models import Meeting, Question
from apps.meeting.models import Response
from collaboard import settings

SOFT_MAX_RESPONSES = 200  # Used in validating the AIs provided response count field

"""
Summary dict structure:
{
    "meeting_title": str,          # Meeting title
    "meeting_description: str,     # Meeting description
    "date": str,                   # Meeting date (formatted)
    "time_created": str,           # Meeting time (formatted)
    "author": str,                 # Meeting director's full name
    "questions_analysis": [        # List of question analysis dicts
        {
            "summary": str,        # 3-sentence response synthesis
            "question": str,       # Original question text
            "response_count": int  # Number of responses
        }
    ],
    "key_takeaways": [str]         # List of actionable takeaway strings
}
"""


class FileTypes(Enum):
    # NOTE: Google Doc files don't end with a traditional prefix like .pdf or .docx
    # ? Google Doc Enum will have to be altered later
    PDF = ".pdf"
    MICROSOFT_WORD = ".docx"

class ExportTypes(Enum):
    # ! This class must be aligned with the return values set in the frontend
    PDF = "pdf"
    MICROSOFT_WORD = "docx"


FILE_NAME_PREFIX: str = "meeting_"
EXPORT_PATH: Path = Path(settings.MEDIA_ROOT) / "exports"


def get_export_path() -> Path:
    """
    Returns the export path where all files are saved
    """
    return EXPORT_PATH


def generate_filename(meeting_id: str, file_type: FileTypes) -> str:
    """
    Returns the dynamically created name of the file
    """
    return f"{FILE_NAME_PREFIX}{meeting_id}{file_type.value}"


def generate_file_path(export_path: Path, filename: str) -> Path:
    """
    Returns the full path to where the file is saved
    """
    return export_path / filename


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


def get_meeting_metadata(data: dict[str, Any]) -> dict[str, Any] | None:
    """
    Extracts the meeting metadata from the provided `data`.

    Meeting Metadata includes:
        - title
        - description
        - date (DD//MM/YYYY)
        - time created (HH:MM)
        - author (firstname + lastname)

    Returns:
        - dict[str, Any]: Meeting Metadata if all fields are valid, None otherwise

    Example Return (if all fields are valid):
        ```
        {
            "title": "Title...",
            "description": "Description...",
            "date": "Date",
            "time_created": "Time Created",
            "author": "John Doe"
        }
        ```
    """
    metadata = {
        "title": data.get("meeting_title", None),
        "description": data.get("meeting_description", None),
        "date": data.get("date", None),
        "time_created": data.get("time_created", None),
        "author": data.get("author", None),
    }
    # Debug to file
    with open('/tmp/debug.log', 'a') as f:
        f.write(f"Raw data keys: {list(data.keys())}\n")
        f.write(f"Metadata: {metadata}\n")
        for key, value in metadata.items():
            if not value:
                f.write(f"FAILED on {key} = {repr(value)}\n")
                return None
    for key, value in metadata.items():
        if not value:
            return None



def get_summarized_meeting_question_analysis(
    data: dict[str, Any],
) -> list[dict[str, Any]] | None:
    """
    Extracts the list of question analysis dictionaries from the provided `data`.

    Additionally validates all fields in each dictionary, ensuring that no field is None

    Each dictionary looks like this:
        ```
        {
            "summary": str,        # 3-sentence response synthesis
            "question": str,       # Original question text
            "response_count": int  # Number of responses
        }
        ```
    Returns:
        - list[dict[str, Any]] | None: The list of question analysis dictionaries if everything is valid, None otherwise.
    """
    questions_analysis_dictionaries: list[dict[str, Any]] | None = data.get(
        "questions_analysis", None
    )
    print(questions_analysis_dictionaries)
    if not questions_analysis_dictionaries:
        return None
    for dictionary in questions_analysis_dictionaries:
        for key, value in dictionary.items():
            # NOTE: Explicit check for response count since 0 is considered Falsy but is a valid response from the AI
            if key == "response_count":
                if not isinstance(value, (str, int)):
                    print(key)
                    return None
                str_response_count: str = str(value)
                if not str_response_count.isdigit():
                    print(str_response_count)
                    return None
                int_response_count: int = int(str_response_count)
                if int_response_count < 0 or int_response_count > SOFT_MAX_RESPONSES:
                    print(int_response_count)
                    return None
            elif not value:
                return None
    return questions_analysis_dictionaries


def get_summarized_meeting_key_takeaways(data: dict[str, Any]) -> list[str] | None:
    """
    Extracts the list of key takeaways strings from the provided `data`

    Additionally ensures that all strings are valid (NOT NONE)

    Key Takeaways looks like this:
        "key_takeaways": [str]         # List of actionable takeaway strings

    Returns:
        - list[str] | None: The list of key takeways if everything is valid, None otherwise.

    Example Return (if all is valid):
        ```
        ["First String", "Second String", ...]
        ```
    """
    key_takeaways: list[str] | None = data.get("key_takeaways", None)
    print(key_takeaways)
    if not key_takeaways:
        return None
    if not all(takeaway and takeaway.strip() for takeaway in key_takeaways):
        return None
    return key_takeaways


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
