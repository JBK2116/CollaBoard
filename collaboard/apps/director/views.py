from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.

@login_required
def dashboard(request):
    context = {}
    return render(request, "director/dashboard.html", context)
