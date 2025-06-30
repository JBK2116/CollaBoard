from django.shortcuts import HttpResponse, render

# Create your views here.

def landing(request) -> HttpResponse:
    return render(request, "base/landing.html")

def register(request) -> HttpResponse:
    return render(request, "base/register.html")

def login(request) -> HttpResponse:
    return render(request, "base/login.html")
