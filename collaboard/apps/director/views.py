from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

# Create your views here.

@login_required
def dashboard(request):
    context = {}
    return render(request, "director/dashboard.html", context)

@login_required
def create_meeting(request):
    # More logic will be implemented later
    if request.method == "POST":
        print(request.POST)
    context = {}
    return render(request, "director/create_meeting.html", context)

@login_required
def edit_meeting(request, meeting_id):
    # More logic will be implemented later
    context = {}
    if request.method == "POST":
        print(request.POST)
    print(meeting_id)
    return render(request, "director/edit_meeting.html", context)

@login_required
def delete_meeting(request, meeting_id):
    # More logic will be implemented later
    context = {}
    if request.method == "POST":
        print(request.POST)
    print(meeting_id)
    return render(request, "director/my_meetings.html", context)

@login_required
def my_meetings(request):
    # More logic will be implemented later
    context = {}
    return render(request, "director/my_meetings.html", context)
