from secrets import randbelow
from typing import cast

from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.db.models import QuerySet
from django.forms import BaseFormSet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.base.models import CustomUser
from apps.director.forms import MeetingForm, QuestionForm, QuestionFormSet
from apps.director.models import Meeting, Question

# Create your views here.


@login_required
def dashboard(request: HttpRequest):
    context = {}
    return render(request, "director/dashboard.html", context)


@login_required
def create_meeting(request: HttpRequest):
    if request.method == "POST":
        meeting_form: MeetingForm | HttpResponse = validate_meeting_form(
            request, MeetingForm(request.POST)
        )
        if isinstance(meeting_form, HttpResponse):
            return meeting_form
        # meeting_form is valid by now
        questions_formset: BaseFormSet[QuestionForm] | HttpResponse = (
            validate_questions_formset(request, QuestionFormSet(request.POST))
        )
        if isinstance(questions_formset, HttpResponse):
            return questions_formset
        # Both forms are valid by now
        user = cast(
            CustomUser, request.user
        )  # User will always be logged in as this due to the function decorator
        try:
            new_meeting = Meeting(
                director=user,
                access_code=generate_meeting_code(),
                title = meeting_form.cleaned_data["title"],
                description=meeting_form.cleaned_data["description"],
                duration=int(meeting_form.cleaned_data["duration"]),
            )  # No need to rerun isvalid, the meeting form has already been cleaned
            new_meeting.save()
            for question in questions_formset:
                new_question = Question(
                    meeting=new_meeting, description=question.cleaned_data["text"]
                )  # No need to rerun isvalid each question has been cleaned
                new_question.save()
        except DatabaseError:
            return redirect(f"{reverse('create-meeting')}?creation_error=true")
        return redirect(f"{reverse('create-meeting')}?created=true")

    else:
        meeting_form = MeetingForm()
        questions_formset = QuestionFormSet()
    return render(
        request,
        "director/create_meeting.html",
        {
            "form": meeting_form,
            "formset": questions_formset,
        },
    )


@login_required
def edit_meeting(request: HttpRequest, meeting_id: str):
    # More logic will be implemented later
    context = {}
    if request.method == "POST":
        print(request.POST)
    print(meeting_id)
    return render(request, "director/edit_meeting.html", context)


@login_required
def delete_meeting(request: HttpRequest, meeting_id: str):
    # More logic will be implemented later
    context = {}
    if request.method == "POST":
        print(request.POST)
    print(meeting_id)
    return render(request, "director/my_meetings.html", context)


@login_required
def my_meetings(request: HttpRequest):
    context = {}
    current_user = cast(CustomUser, request.user)
    all_meetings: QuerySet[Meeting] = Meeting.objects.filter(director=current_user)
    context.update({"meetings": all_meetings})
    return render(request, "director/my_meetings.html", context)

"""
Below are helper functions for these views
"""

def validate_meeting_form(
    request: HttpRequest, form: MeetingForm
) -> MeetingForm | HttpResponse:
    valid = form.is_valid()
    if valid is False:
        context = {"meeting_errors": form.errors, "creation_error": True}
        return render(request, "base/create_meeting.html", context)
    return form


def validate_questions_formset(
    request: HttpRequest, formset: BaseFormSet
) -> BaseFormSet | HttpResponse:
    valid = formset.is_valid()
    if valid is False:
        context = {"formset_errors": formset.errors, "creation_error": True}
        return render(request, "base/create_meeting.html", context)
    return formset


def generate_meeting_code() -> str:
    return "".join(str(randbelow(10)) for _ in range(8))
