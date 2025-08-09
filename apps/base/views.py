import time
from secrets import randbelow
from typing import Any, cast

from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django_ratelimit.decorators import ratelimit

from apps.base.forms import UserLoginForm, UserRegisterForm, VerifyEmailForm
from apps.base.models import CustomUser
from collaboard import settings


# Create your views here.
def ratelimited(request: HttpRequest, exception: Exception) -> HttpResponse:
    print("RATE LIMIT VIEW CALLED!")  # Add this debug line
    return render(request, template_name="403.html", status=403)


def landing_page(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, template_name="index.html")


@ratelimit(group="limit_per_hour", key="ip", rate="20/h", method=["POST"], block=True)
@ratelimit(group="limit_per_minute", key="ip", rate="5/m", method=["POST"], block=True)
def register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form_result = _validate_register_form(
            request=request, form=UserRegisterForm(request.POST)
        )
        if isinstance(form_result, HttpResponse):
            return form_result  # User provided invalid info OR an error occurred

        form = form_result
        if _user_exists(form.cleaned_data["email"]):
            return render(
                request,
                template_name="base/register.html",
                context={
                    "form": form,
                    "email_exists": "An account already exists with that email",
                },
            )
        verification_code: str = _generate_verification_code()
        request.session["pending_user_info"] = {
            "first_name": form.cleaned_data["first_name"],
            "last_name": form.cleaned_data["last_name"],
            "email": form.cleaned_data["email"],
            "password": make_password(password=form.cleaned_data["password1"]),
            "verification_code": verification_code,
            "expires_in": time.monotonic() + 60 * 10,  # Ten Minutes
        }
        _send_email(
            verification_code=verification_code, user_email=form.cleaned_data["email"]
        )
        return redirect("verify-email")
    else:
        form = UserRegisterForm()
        return render(
            request, template_name="base/register.html", context={"form": form}
        )


def _send_email(verification_code: str, user_email: str):
    subject: str = "Collaboard - Verify Your Account"
    text_content: str = f"Verify your account to begin creating meetings! Here's your code: {verification_code}"
    html_message = render_to_string(
        template_name="base/verification_code_email.html",
        context={"verification_code": verification_code},
    )
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[user_email],
    )
    msg.attach_alternative(content=html_message, mimetype="text/html")
    # TODO: Handle this better
    try:
        msg.send()
    except Exception:
        return redirect("landing")


@ratelimit(group="limit_per_hour", key="ip", rate="20/h", method=["POST"], block=True)
@ratelimit(group="limit_per_minute", key="ip", rate="10/m", method=["POST"], block=True)
def verify_email(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")
    context: dict[str, Any] = {}
    if request.method == "POST":
        form_result: VerifyEmailForm | HttpResponse = _validate_email_form(
            request=request, form=VerifyEmailForm(request.POST)
        )
        if isinstance(form_result, HttpResponse):
            return form_result  # User submitted invalid info OR an error occurred
        form = form_result

        pending_user_info: dict[str, Any] | HttpResponse = _get_pending_user_fields(
            request=request, data=request.session.get("pending_user_info", {})
        )
        if isinstance(pending_user_info, HttpResponse):
            return pending_user_info  # Pending info is invalid or missing entirely
        # NOTE: All fields are validated at this point
        current_time = time.monotonic()
        if pending_user_info["expires_in"] - current_time < 0:
            context.update({"code_expired": True})
            return render(
                request, template_name="base/verify_email.html", context=context
            )
        if (
            pending_user_info["verification_code"]
            != form.cleaned_data["verification_code"]
        ):
            context.update({"invalid_code": True})
            return render(
                request, template_name="base/verify_email.html", context=context
            )
        # NOTE: Now the user has successfully verified their account
        user: CustomUser = CustomUser(
            first_name=pending_user_info["first_name"],
            last_name=pending_user_info["last_name"],
            email=pending_user_info["email"],
            password=pending_user_info["password"],
        )
        user.save()
        login(request, user)
        return redirect("dashboard")
    else:
        form: VerifyEmailForm = VerifyEmailForm()
        context.update({"form": form})
        return render(request, template_name="base/verify_email.html", context=context)


@ratelimit(group="limit_per_hour", key="ip", rate="20/h", method=["POST"], block=True)
@ratelimit(group="limit_per_minute", key="ip", rate="5/m", method=["POST"], block=True)
def login_user(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form_result = _validate_login_form(request, form=UserLoginForm(request.POST))
        if isinstance(form_result, HttpResponse):
            return form_result  # User inputted invalid info or an error occurred

        # At this point, we know form_result is a UserLoginForm
        form = form_result
        user = authenticate(
            request,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        if not user:
            return render(
                request,
                template_name="base/login.html",
                context={"form": form, "invalid_error": "Invalid email or password"},
            )
        login(request, user=user)
        if request.POST.get("remember_me"):
            request.session.set_expiry(604800)  # One week
        else:
            request.session.set_expiry(0)  # expire on browser close
        return redirect("dashboard")

    else:
        form = UserLoginForm()
        return render(request, "base/login.html", context={"form": form})


def _get_pending_user_fields(
    request: HttpRequest, data: Any | None
) -> dict[str, Any] | HttpResponse:
    """
    Ensures that all fields created by request.session in the `register_user` view is valid

    IMPORTANT: data must be a dictionary and must match the request.session dictionary created in the view

    Returns:
        - dict[str, Any] | None: data dictionary if valid else an HttpResponse
    """
    # NOTE: required fields must match exactly with the request.session dictionary created in the register view
    if not data:
        return redirect("register")
    user_data = cast(dict[str, Any], data)
    required_fields: list[str] = [
        "first_name",
        "last_name",
        "email",
        "password",
        "verification_code",
        "expires_in",
    ]
    missing_or_none = [
        field
        for field in required_fields
        if field not in user_data or user_data[field] is None
    ]
    if missing_or_none:
        return redirect("register")
    return user_data


def _validate_register_form(
    request: HttpRequest, form: UserRegisterForm
) -> UserRegisterForm | HttpResponse:
    """Validates form and returns it if valid, otherwise re-renders with errors."""
    if form.is_valid():
        return form
    return render(request, template_name="base/register.html", context={"form": form})


def _validate_email_form(
    request: HttpRequest, form: VerifyEmailForm
) -> VerifyEmailForm | HttpResponse:
    """Validates form and returns it if valid, otherwise re-renders with errors."""
    if form.is_valid():
        return form
    return render(
        request,
        template_name="base/verify_email.html",
        context={"form": form, "invalid_code": True},
    )


def _validate_login_form(
    request: HttpRequest, form: UserLoginForm
) -> UserLoginForm | HttpResponse:
    """Validates form and returns it if valid, otherwise re-renders with errors."""
    if form.is_valid():
        return form
    return render(request, template_name="base/login.html", context={"form": form})


def _user_exists(email: str) -> bool:
    """
    Performs a simple existence check query in the database
    by trying to find a user object that has the same email value
    as the one provided to the function
    """
    return CustomUser.objects.filter(email=email).exists()


def _generate_verification_code() -> str:
    """
    Returns a random 8 digit numerical string
    """
    # Returns a random 8 digit numerical string
    return "".join(str(randbelow(10)) for _ in range(8))
