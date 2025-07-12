from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import authenticate, login
from apps.base.forms import UserRegisterForm, UserLoginForm
from apps.base.models import CustomUser

# Create your views here.


def landing_page(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, template_name="index.html")


def register_user(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form_result = validate_register_form(
            request=request, form=UserRegisterForm(request.POST)
        )
        if isinstance(form_result, HttpResponse):
            return form_result  # User inputted invalid info or an error occurred

        # At this point, we know form_result is a UserRegisterForm
        form = form_result
        if user_exists(
            form.cleaned_data["email"]
        ):  # Fixed: was using password1 instead of email
            return render(
                request,
                template_name="base/register.html",
                context={
                    "form": form,
                    "email_exists": "An account already exists with that email",
                },
            )
        user = CustomUser(
            email=form.cleaned_data["email"],
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
        )
        user.set_password(raw_password=form.cleaned_data["password1"])
        user.save()
        return redirect("dashboard")
    else:
        # Request is a simple GET method
        form = UserRegisterForm()
        return render(
            request, template_name="base/register.html", context={"form": form}
        )


def login_user(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form_result = validate_login_form(request, form=UserLoginForm(request.POST))
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


def validate_register_form(
    request: HttpRequest, form: UserRegisterForm
) -> UserRegisterForm | HttpResponse:
    """Validates form and returns it if valid, otherwise re-renders with errors."""
    if form.is_valid():
        return form
    return render(request, template_name="base/register.html", context={"form": form})


def validate_login_form(
    request: HttpRequest, form: UserLoginForm
) -> UserLoginForm | HttpResponse:
    """Validates form and returns it if valid, otherwise re-renders with errors."""
    if form.is_valid():
        return form
    return render(request, template_name="base/login.html", context={"form": form})


def user_exists(email: str) -> bool:
    """
    Performs a simple existence check query in the database
    by trying to find a user object that has the same email value
    as the one provided to the function
    """
    return CustomUser.objects.filter(email=email).exists()
