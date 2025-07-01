from typing import Any

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import HttpResponse, redirect, render
from django.urls import reverse

from apps.base.models import CustomUser

# Create your views here.


def landing(request) -> HttpResponse:
    return render(request, "base/landing.html")


def register(request) -> HttpResponse:
    context: dict[str, Any] = {}
    if request.method == "POST":
        fields = ["first_name", "last_name", "email", "password1", "agree_terms"]
        data: dict[str, str] = {
            field: request.POST.get(field, "").strip()
            for field in fields  # Stores all data from register account form
        }
        context.update({"data": data})
        # Check for an existing user with the same email
        if CustomUser.objects.filter(email=data.get("email")).exists():
            context.update({"user_exists": True})
            return render(request, "base/register.html", context)
        # Create the new user
        new_user = CustomUser(
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            email=data.get("email"),
        )
        try:
            password: str | None = data.get("password1")
            if not password:
                context.update({"missing_password": True})
                return render(
                    request,
                    "base/register.html",
                    context,
                )
            validate_password(password, user=new_user)
            new_user.set_password(password)  # Hash the password
            # By now all fields have been validated
            new_user.full_clean()  # Validate firstname, lastname and email
            new_user.save()  # Save the user to the database
            return redirect(
                f"{reverse('login')}?created=true"
            )  # redirect the user to login with query parameter for special card
        except ValidationError as e:
            context.update(
                {
                    "form_errors": e.message_dict,
                    "password_errors": e.messages,
                }
            )
            return render(
                request,
                "base/register.html",
                context,
            )
    return render(request, "base/register.html", context)  # Request is a simple GET request


def login(request) -> HttpResponse:
    if request.method == "POST":
        print("POST")
    just_created = request.GET.get("created") == "true"
    return render(request, "base/login.html", {"just_created": just_created})
