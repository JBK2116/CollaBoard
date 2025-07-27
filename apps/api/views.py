import json
import os
from typing import Any

from django.db import IntegrityError
from django.http import HttpRequest, JsonResponse
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletion

from apps.api import utils
from apps.director.models import Meeting, Question
from apps.meeting.models import Response

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
        questions: list[Question] | None = meeting_data.get("questions", None)
        responses: list[Response] | None = meeting_data.get("responses", None)
        if not meeting or not questions or not responses:
            return JsonResponse(data={"type": "error"})

        question_response_dictionary: dict[str, Any] = utils.format_question_responses(
            questions=questions, responses=responses
        )
        formatted_times: dict[str, str] = utils.format_meeting_time(
            time=meeting.created_at
        )

        print(meeting.title)
        print(meeting.director.get_full_name())
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
                    "summary": "[3-sentence synthesis of all responses. Highlight: 
                                - Key agreements/disagreements
                                - Actionable insights
                                - Unresolved questions]",
                    "response_count": [integer]
                    }}
                ],
                "key_takeaways": [
                    "[Most important decision]",
                    "[Critical unresolved issue]",
                    "[Next step with owner if mentioned]"
                ]
                }}

                Rules:
                - Keep summaries CONCISE but SPECIFIC
                - Include NUMBERS when available ("3 team members opposed")
                - Flag [DISAGREEMENT] when opinions diverge
                - Never invent details not in the source
                - ONLY analyze the provided data, do not generate metadata

                Meeting data to analyze:
                {json.dumps(question_response_dictionary, indent=2)}
                """

        client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_SECRET_KEY"))
        response: ChatCompletion = client.chat.completions.create(
            model="gpt-3.5-turbo",
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
                "date": formatted_times["created_at"],
                "time_created": formatted_times["time_created"],
                "author": meeting.director.get_full_name(),
                "questions_analysis": ai_analysis.get("questions_analysis", []),
                "key_takeaways": ai_analysis.get("key_takeaways", []),
            }

            print(final_summary)

            meeting.summarized_meeting = final_summary
            meeting.save()
            

        except (json.JSONDecodeError, IntegrityError):
            return JsonResponse(data={"type": "error"})

        return JsonResponse(data={})
    else:
        return JsonResponse(data={"type": "error"})


def export_meeting(request: HttpRequest, meeting_id: str) -> JsonResponse:
    if request.method == "POST":
        try:
            data: dict[str, Any] = json.loads(request.body)
            export_type: str | None = data.get("type", None)
            if not export_type:
                return JsonResponse(data={"type": "error"})
            print(export_type)
            return JsonResponse(data={})
        except json.JSONDecodeError:
            return JsonResponse(data={})
    return JsonResponse(data={})
