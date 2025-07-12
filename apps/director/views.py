from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from apps.director.forms import CreateMeetingForm, QuestionFormSet
from django.contrib.auth.decorators import login_required


# Create your views here.

@login_required
def create_meeting(request: HttpRequest) -> HttpResponse:
    context = {}
    if request.method == "POST":
        # More handling will be done later
        meeting_form = CreateMeetingForm(request.POST)
        question_forms = QuestionFormSet(request.POST)
        print(meeting_form)
        print(question_forms)
        return redirect("create-meeting")
    else:
        # Simple get request
        meeting_form = CreateMeetingForm()
        question_formset = QuestionFormSet()
        context.update({"meeting_form": meeting_form, "question_formset": question_formset})
        return render(request, template_name="director/create_meeting.html", context=context)
@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    context = {}
    return render(request, template_name="director/dashboard.html", context=context)

@login_required
def account(request: HttpRequest) -> HttpResponse:
    context = {}
    return render(request, template_name="director/account.html", context=context)
    