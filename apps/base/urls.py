from django.urls import path
from apps.base import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
]