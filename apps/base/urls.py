from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.base import views

urlpatterns = [
    path("", views.landing_page, name="landing"),
    path("register/", views.register, name="register"),
    path("verify-email/", views.verify_email, name="verify-email"),
    path("login/", views.login_user, name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("forgot-password/", views.forgot_password, name="forgot-password"),
    path("reset-password/<str:token>/new/", views.reset_password, name="reset-password")
]
