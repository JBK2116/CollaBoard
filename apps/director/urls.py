from django.urls import URLPattern, path

from apps.director import views

urlpatterns: list[URLPattern] = [
    path("dashboard/", view=views.dashboard, name="dashboard"),
    path("create-meeting/", view=views.create_meeting, name="create-meeting"),
    path("delete-account/", view=views.delete_account, name="delete-account"),
    path("account/", view=views.account, name="account"),
]
