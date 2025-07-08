from django.shortcuts import render


# Create your views here.
def host_meeting(request, meeting_id: str):
    context = {"meeting_id": meeting_id}
    return render(request, "meeting/live_control.html", context)
