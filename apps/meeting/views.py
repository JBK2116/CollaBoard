from django.contrib.auth.decorators import login_not_required, login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.director.models import Meeting


# Create your views here.
@login_required
def host_meeting(request: HttpRequest, meeting_id: str) -> HttpResponse:
    try:
        meeting: Meeting = Meeting.objects.get(id=meeting_id)
        return render(
            request,
            template_name="meeting/meeting_host.html",
            context={"meeting": meeting},
        )
    except Meeting.DoesNotExist:
        return redirect(f"{reverse('create-meeting')}?creation_error=true")


@login_not_required
def participant_meeting(request: HttpRequest, access_code: str) -> HttpResponse:
    participant_name: str | None = request.POST.get("participantName", None)
    if not participant_name or len(participant_name) > 30:
        raise Http404("Invalid Name")
    try:
        meeting: Meeting = Meeting.objects.get(access_code=access_code)
        return render(
            request,
            template_name="meeting/meeting_participant.html",
            context={"meeting": meeting, "participant_name": participant_name},
        )
    except Meeting.DoesNotExist:
        raise Http404("Meeting not found")


@login_required
def post_meeting_host(request: HttpRequest, meeting_id: str) -> HttpResponse:
    try:
        meeting: Meeting = Meeting.objects.get(id=meeting_id)
        return render(
            request,
            template_name="meeting/meeting_summary.html",
            context={"meeting": meeting},
        )
    except Meeting.DoesNotExist:
        raise Http404("Meeting not found")


def meeting_locked(request: HttpRequest) -> HttpResponse:
    return render(request, template_name="meeting/meeting_locked.html")


def post_meeting_participant(request: HttpRequest) -> HttpResponse:
    return render(request, template_name="meeting/post_meeting.html")
