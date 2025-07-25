import json
from typing import Any

from django.http import HttpRequest, JsonResponse

# Create your views here.


def summarize_meeting(request: HttpRequest, meeting_id: str) -> JsonResponse:
    if request.method == "GET":
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
            return JsonResponse(
                data={}
            )
        except json.JSONDecodeError:
            return JsonResponse(data={})
    return JsonResponse(data={})
