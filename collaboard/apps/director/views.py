from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import MeetingForm, QuestionFormSet

# Create your views here.

@login_required
def dashboard(request: HttpRequest):
    context = {}
    return render(request, "director/dashboard.html", context)

@login_required
def create_meeting(request: HttpRequest):
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        formset = QuestionFormSet(request.POST)
        print(request.POST)
    else:
        form = MeetingForm()
        formset = QuestionFormSet()
    return render(request, 'director/create_meeting.html', {
        'form': form,
        'formset': formset,
    })

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
    # More logic will be implemented later
    context = {}
    return render(request, "director/my_meetings.html", context)
