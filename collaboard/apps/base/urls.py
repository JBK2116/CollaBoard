from django.contrib import admin  # noqa: F401
from django.urls import path  # noqa: F401

from apps.base import views

urlpatterns = [
    path("", views.landing, name="landing"), # Homepage Path
    path("register/", views.register, name="register"), # Register An Account Page
]
