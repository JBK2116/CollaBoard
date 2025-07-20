from django.contrib.auth.decorators import login_not_required, login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.director.models import Meeting


# Create your views here.
@login_required
def host_meeting(request: HttpRequest, meeting_id: str) -> HttpResponse:
    # More info will be added later
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
    # More info will be added later
    try:
        meeting: Meeting = Meeting.objects.get(access_code=access_code)
        return render(
            request,
            template_name="meeting/meeting_participant.html",
            context={"meeting": meeting},
        )
    except Meeting.DoesNotExist:
        raise Http404("Meeting not found")

def meeting_locked(request: HttpRequest) -> HttpResponse:
    return render(request, template_name="meeting/meeting_locked.html")