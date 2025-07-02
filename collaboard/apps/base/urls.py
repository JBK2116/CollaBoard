from django.contrib.auth.views import LogoutView
from django.urls import path  # noqa: F401

from apps.base import views

urlpatterns = [
    path("", views.landing, name="landing"), # Homepage Path
    path("register/", views.register, name="register"), # Register An Account Page
    path("login/", views.login_user, name="login"), # User Login Page
    path("logout/", LogoutView.as_view(), name="logout")
]
