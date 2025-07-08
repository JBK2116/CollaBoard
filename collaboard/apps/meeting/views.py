from uuid import UUID

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from apps.director.models import Meeting


# Create your views here.
def host_meeting(request: HttpRequest, meeting_id: str) -> HttpResponse:
    try:
        meeting = Meeting.objects.get(id=UUID(meeting_id))
    except Meeting.DoesNotExist:
        raise Http404("Meeting not found...")  # noqa: B904

    context = {"meeting": meeting}
    return render(request, "meeting/live_control.html", context)
