from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.

@login_required
def dashboard(request):
    context = {}
    return render(request, "director/dashboard.html", context)

@login_required
def create_meeting(request):
    if request.method == "POST":
        print(request.POST)
    context = {}
    return render(request, "director/create_meeting.html", context)

def edit_meeting(request, meeting_id):
    context = {}
    print(meeting_id)
    return render(request, "director/edit_meeting.html", context)
