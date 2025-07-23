from django.urls import path

from apps.meeting import views

urlpatterns = [
    path("<str:meeting_id>/host/", view=views.host_meeting, name="host-meeting"),
    path(
        "<str:access_code>/participant/",
        view=views.participant_meeting,
        name="participant-meeting",
    ),
    path("locked/", view=views.meeting_locked, name="meeting-locked"),
    path("<str:meeting_id>/ended/", views.post_meeting_host, name="post-meeting-host"),
    path("ended/", view=views.post_meeting_participant, name="post-meeting"),
]
