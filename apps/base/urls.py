from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.base import views

urlpatterns = [
    path("", views.landing_page, name="landing"),
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", LogoutView.as_view(), name="logout")
]
