from django.urls import path

from apps.api import views

urlpatterns = [
    path(
        "<str:meeting_id>/summarize/",
        view=views.summarize_meeting,
        name="summarize-meeting",
    ),
    path("<str:meeting_id>/export/", view=views.export_meeting, name="export-meeting"),
]
