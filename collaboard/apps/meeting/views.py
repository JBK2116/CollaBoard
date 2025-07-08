from typing import cast
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from apps.base.models import CustomUser
from apps.director.models import Meeting


# Create your views here.
@login_required
def host_meeting(request: HttpRequest, meeting_id: str) -> HttpResponse:
    user = cast(CustomUser, request.user)
    try:
        meeting = Meeting.objects.get(id=UUID(meeting_id), director=user)
    except Meeting.DoesNotExist:
        raise Http404("Meeting not found...")  # noqa: B904

    context = {"meeting": meeting}
    return render(request, "meeting/live_control.html", context)

def join_meeting(request: HttpRequest, code: str) -> HttpResponse:
    try:
        meeting = Meeting.objects.get(access_code=int(code))
    except Meeting.DoesNotExist:
        raise Http404("Meeting not found... ")  # noqa: B904
    context = {"meeting": meeting}
    return render(request, "meeting/live_participant.html", context)
