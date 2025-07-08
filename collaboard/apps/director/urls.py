from django.urls import path

from apps.director import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("create-meeting/", views.create_meeting, name="create-meeting"),
    path("edit-meeting/<str:meeting_id>/", views.edit_meeting, name="edit-meeting"),
    path("delete-meeting/<str:meeting_id>/", views.delete_meeting, name="delete-meeting"),
    path("my-meetings", views.my_meetings, name="my-meetings"),
    path("live-sessions/", views.live_session, name="live-sessions"),
]
