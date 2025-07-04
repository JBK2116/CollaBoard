from django.urls import path

from apps.director import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("create-meeting/", views.create_meeting, name="create-meeting"),
    path("edit-meeting/<int:meeting_id>/", views.edit_meeting, name="edit-meeting"),
]
