from django.urls import URLPattern, path

from apps.director import views

urlpatterns: list[URLPattern] = [
    path("dashboard/", view=views.dashboard, name="dashboard"),
    path("create-meeting/", view=views.create_meeting, name="create-meeting"),
    path("account/", view=views.account, name="account"),
]
