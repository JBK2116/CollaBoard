import json
import os
import uuid
from pathlib import Path
from typing import Any

from django.db import IntegrityError
from django.http import FileResponse, HttpRequest, JsonResponse
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletion

from apps.api import utils
from apps.api.docx_generator import generate_docx
from apps.api.pdf_generator import generate_pdf
from apps.director.models import Meeting, Question
from apps.meeting.models import Response
from collaboard import settings

# Create your views here.
load_dotenv()


def summarize_meeting(request: HttpRequest, meeting_id: str) -> JsonResponse:
    if request.method == "GET":
        meeting_data: dict[str, Any] | None = utils.get_meeting_data(
            meeting_id=meeting_id
        )
        if not meeting_data:
            return JsonResponse(data={"type": "error"})

        meeting: Meeting | None = meeting_data.get("meeting", None)
        if not meeting:
            return JsonResponse(data={"type": "error"})

        # NOTE: Meetings are to be summarized only once! Always check before u generate a summary
        # ! Make sure to uncomment this check before u deploy
        # if meeting.summarized_meeting and meeting.summarized_meeting != {}:
        #     print("Meeting already summarized")
        #     return JsonResponse(data={"type": "success"})

        questions: list[Question] | None = meeting_data.get("questions", None)
        responses: list[Response] | None = meeting_data.get("responses", None)
        if not questions or not responses:
            return JsonResponse(data={"type": "error"})

        question_response_dictionary: dict[str, Any] = utils.format_question_responses(
            questions=questions, responses=responses
        )
        formatted_times: dict[str, str] = utils.format_meeting_time(
            time=meeting.created_at
        )
        print(formatted_times)

        # ! Summarization PROMPT - only ask AI to analyze questions, not generate metadata
        # NOTE: Look into the util's to see how the AI summary response is fully structured
        summary_prompt = f"""
        Analyze the following meeting questions and responses, then provide a JSON summary of ONLY the questions analysis and key takeaways.

        DO NOT generate meeting metadata (title, date, author) - I will add those separately.

        Format EXACTLY like this (escape all quotes):
        {{
        "questions_analysis": [
            {{
            "question": "[EXACT original question text]",
            "summary": "[4-5 sentence comprehensive analysis that includes:
                        - Opening sentence synthesizing the overall theme/consensus
                        - Specific response perspectives using descriptors ('one participant noted', 'another emphasized')
                        - Clear identification of agreements, disagreements, or patterns
                        - Actionable insights or decisions emerging from responses
                        - Any unresolved questions or conflicting viewpoints]",
            "response_count": [integer]
            }}
        ],
        "key_takeaways": [
            "[Most important decision or consensus with context]",
            "[Critical unresolved issue requiring follow-up]",
            "[Strategic insight or pattern identified across responses]",
            "[Next step or recommendation emerging from discussions]"
        ]
        }}

        Rules:
        - Each summary should be 4-5 complete sentences for comprehensive context
        - Lead with overall consensus/theme, then explore different viewpoints
        - Use descriptors like "one participant suggested", "multiple responses indicated", "another viewpoint emphasized"
        - Quantify agreement patterns ("three of four responses focused on...")
        - Use specific numbers and metrics when available
        - Flag clear disagreements with [DISAGREEMENT] at start of summary
        - Identify trends across anonymous responses
        - Highlight actionable items and emerging decisions
        - Never invent details not in the source
        - Make summaries rich enough to stand alone when read in sequence

        Meeting data to analyze:
        {json.dumps(question_response_dictionary, indent=2)}
        """

        client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_SECRET_KEY"))
        response: ChatCompletion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a meeting analysis assistant. You analyze questions and responses but never generate meeting metadata like titles, dates, or author names.",
                },
                {"role": "user", "content": summary_prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        response_str: str | None = response.choices[0].message.content
        if not response_str:
            return JsonResponse(data={"type": "error"})

        try:
            ai_analysis: dict[str, Any] = json.loads(response_str)

            # NOTE: Manually reconstruct the final summary to minimize ai hallucinations
            final_summary = {
                "meeting_title": meeting.title,
                "meeting_description": meeting.description,
                "date": formatted_times["created_at"],
                "time_created": formatted_times["time_created"],
                "author": meeting.director.get_full_name(),
                "questions_analysis": ai_analysis.get("questions_analysis", []),
                "key_takeaways": ai_analysis.get("key_takeaways", []),
            }

            meeting.summarized_meeting = final_summary
            meeting.save()

        except (json.JSONDecodeError, IntegrityError):
            return JsonResponse(data={"type": "error"})

        return JsonResponse(data={})
    else:
        return JsonResponse(data={"type": "error"})


def export_meeting(request: HttpRequest, meeting_id: str) -> JsonResponse:
    if request.method == "POST":
        export_type: str | None = _get_export_type(request.body)
        if not export_type:
            return JsonResponse(data={"type": "error"})

        meeting: Meeting | None = _get_meeting_by_id(meeting_id=meeting_id)
        if not meeting:
            return JsonResponse(data={"type": "error"})

        if meeting.summarized_meeting and meeting.summarized_meeting == {}:
            print("Meeting not yet summarized")
            return JsonResponse(
                data={"type": "error", "message": "Meeting not summarized yet"}
            )

        result: tuple[bool, str | None] = (False, None)

        match export_type:
            case utils.ExportTypes.PDF.value:
                result = generate_pdf(meeting.summarized_meeting, str(meeting_id))
            case utils.ExportTypes.MICROSOFT_WORD.value:
                result = generate_docx(meeting.summarized_meeting, str(meeting_id))
            case _:
                pass

        if not result[0] or not result[1]:
            return JsonResponse(data={"type": "error"})
        else:
            return JsonResponse(data={"type": "success", "download_url": result[1]})
    else:
        return JsonResponse(data={"type": "error"})


def download_file(request: HttpRequest, filename: str) -> FileResponse:
    # NOTE: response ensures that the file is downloaded on the user's device
    file_path: Path = settings.MEDIA_ROOT / "exports" / filename
    response = FileResponse(open(file=file_path, mode="rb"), as_attachment=True)
    return response


def _get_meeting_by_id(meeting_id: str) -> Meeting | None:
    """
    Fetches a meeting object from the database via
    filtering by the provided `meeting_id`

    Returns: Meeting if found, otherwise None
    """
    try:
        meeting: Meeting | None = Meeting.objects.get(id=uuid.UUID(meeting_id))
        return meeting
    except Meeting.DoesNotExist:
        return None


# ! EXPORT TYPES ARE EITHER `pdf` or `docx`
# ! IT MUST ALIGN WITH THE FRONTEND
def _get_export_type(data: bytes) -> str | None:
    """
    Extracts the `type` value from the provided data
    Assumes that the value will be a valid export type.
    """
    try:
        json_data: dict[str, Any] = json.loads(data)
        export_type: str | None = json_data.get("type", None)
        if not export_type:
            return None
        return export_type
    except json.JSONDecodeError:
        return None
