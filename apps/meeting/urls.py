from django.contrib import admin
from django.urls import path
from apps.meeting import views

urlpatterns = [
    path("<str:meeting_id>/host/", view=views.host_meeting, name="host-meeting"),
    path(
        "<str:access_code>/participant/",
        view=views.participant_meeting,
        name="participant-meeting",
    ),
]
