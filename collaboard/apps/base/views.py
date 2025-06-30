from django.shortcuts import HttpResponse, render  # noqa: F401

# Create your views here.

def landing(request) -> HttpResponse:
    return render(request, "base/landing.html")
