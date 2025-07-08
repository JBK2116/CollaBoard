from secrets import randbelow
from typing import cast
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.db.models import QuerySet
from django.forms import BaseFormSet
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.base.models import CustomUser
from apps.director.forms import MeetingForm, QuestionForm, QuestionFormSet
from apps.director.models import Meeting, Question, Response

# Create your views here.


@login_required
def dashboard(request: HttpRequest):
    user = cast(CustomUser, request.user)
    total_meetings = Meeting.count_published_for_director(user)
    participant_count = Meeting.get_total_responses(user)
    success_rate = Meeting.get_meeting_success_rate(user)
    average_response_time = Response.get_average_response_time(user)
    context = {
        "total_meetings": total_meetings,
        "participant_count": participant_count,
        "success_rate": success_rate,
        "response_time": average_response_time,
    }
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
                title=meeting_form.cleaned_data["title"],
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
    try:
        meeting = Meeting.objects.get(id=UUID(meeting_id))
    except Meeting.DoesNotExist:
        raise Http404("Meeting not found...")  # noqa: B904

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
        try:
            # Update meeting details
            meeting.title = meeting_form.cleaned_data["title"]
            meeting.description = meeting_form.cleaned_data["description"]
            meeting.duration = int(meeting_form.cleaned_data["duration"])
            meeting.save()

            # Delete existing questions and create new ones
            Question.objects.filter(meeting=meeting).delete()
            for question in questions_formset:
                new_question = Question(
                    meeting=meeting, description=question.cleaned_data["text"]
                )
                new_question.save()
        except DatabaseError:
            return redirect(
                f"{reverse('edit-meeting', args=[meeting_id])}?update_error=true"
            )
        return redirect(f"{reverse('edit-meeting', args=[meeting_id])}?updated=true")
    else:
        # Pre-fill the meeting form with existing data
        initial_meeting_data = {
            "title": meeting.title,
            "description": meeting.description,
            "duration": str(meeting.duration),
        }
        meeting_form = MeetingForm(initial=initial_meeting_data)

        # Pre-fill the questions formset with existing questions
        existing_questions = Question.objects.filter(meeting=meeting)
        initial_questions_data = []
        for question in existing_questions:
            initial_questions_data.append({"text": question.description})

        questions_formset = QuestionFormSet(initial=initial_questions_data)

    context = {
        "form": meeting_form,
        "formset": questions_formset,
        "meeting": meeting,
    }
    return render(request, "director/edit_meeting.html", context)


@login_required
def delete_meeting(request: HttpRequest, meeting_id: str):
    context = {}
    if request.method == "POST":
        try:
            meeting = Meeting.objects.get(id=UUID(meeting_id))
        except Meeting.DoesNotExist:
            raise Http404("Meeting not found")  # noqa: B904
        # By now the meeting obj exists
        meeting.delete()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        else:
            return redirect("my-meetings")
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
