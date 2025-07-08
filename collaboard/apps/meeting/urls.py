from django.urls import path

from apps.meeting import views

urlpatterns = [
    path("host/<str:meeting_id>/", views.host_meeting, name="host-meeting"),
    path("join/<str:code>/", views.join_meeting, name="join-meeting"),
]
