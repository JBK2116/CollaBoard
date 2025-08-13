from secrets import randbelow
from typing import cast

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django_ratelimit.decorators import ratelimit

from apps.base.models import CustomUser
from apps.director.forms import CreateMeetingForm, QuestionFormSet
from apps.director.models import Meeting, Question


@login_required
# @ratelimit(
#     group="limit_per_day", key="user_or_ip", rate="20/d", method=["POST"], block=True
# )
# @ratelimit(
#     group="limit_per_hour", key="user_or_ip", rate="10/h", method=["POST"], block=True
# )
# @ratelimit(
#     group="limit_per_minute", key="user_or_ip", rate="3/m", method=["POST"], block=True
# )
def create_meeting(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        # More handling will be done later
        meeting_form = CreateMeetingForm(request.POST)
        question_formset = QuestionFormSet(request.POST)
        if not meeting_form.is_valid() or not question_formset.is_valid():
            return render(
                request,
                template_name="director/create_meeting.html",
                context={
                    "meeting_form": meeting_form,
                    "question_formset": question_formset,
                },
            )
        user = cast(CustomUser, request.user)
        try:
            meeting = Meeting(
                director=user,
                access_code=generate_access_code(),
                title=meeting_form.cleaned_data["title"],
                description=meeting_form.cleaned_data["description"],
                duration=int(meeting_form.cleaned_data["duration"]),
            )
            meeting.save()
        except (IntegrityError, ValidationError):
            return redirect(f"{reverse(viewname='create-meeting')}?creation_error=true")

        try:
            with transaction.atomic():
                for index, question in enumerate(question_formset, start=1):
                    new_question = Question(
                        meeting=meeting,
                        description=question.cleaned_data["description"],
                        position=index,
                    )
                    new_question.save()
        except (IntegrityError, ValidationError):
            return redirect(f"{reverse(viewname='create-meeting')}?creation_error=true")

        return redirect(
            to=f"{reverse('host-meeting', kwargs={'meeting_id': str(meeting.id)})}"
        )
    else:
        # Simple get request
        meeting_form = CreateMeetingForm()
        question_formset = QuestionFormSet()
        return render(
            request,
            template_name="director/create_meeting.html",
            context={
                "meeting_form": meeting_form,
                "question_formset": question_formset,
            },
        )


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, template_name="director/dashboard.html", context={})


@login_required
def account(request: HttpRequest) -> HttpResponse:
    return render(request, template_name="director/account.html", context={})


@login_required
def delete_account(request: HttpRequest) -> HttpResponse:
    # NOTE: This view is supposed to be accessible solely via POST requests
    if request.method == "POST":
        user = cast(CustomUser, request.user)
        try:
            user.delete()
            return redirect(to="landing")
        except IntegrityError:
            return redirect(to=f"{reverse('account')}?deletion_failed=true")
    else:
        return redirect(to="dashboard")


def generate_access_code() -> str:
    # NOTE: Returns a random 8 digit numerical string
    return "".join(str(randbelow(10)) for _ in range(8))
