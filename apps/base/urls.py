from django.urls import path
from apps.base import views

urlpatterns = [
    path("", views.landing, name="landing"),
]