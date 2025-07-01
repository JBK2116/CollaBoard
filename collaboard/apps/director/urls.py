from django.urls import path

from apps.director import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
]
