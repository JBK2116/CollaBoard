from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from typing import Any

# Create your views here.

def landing(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html") 

def register(request: HttpRequest) -> HttpResponse:
    context: dict[str, Any] = {}
    if request.method == "POST":
        print(request.POST)
    return render(request, "base/register.html", context)

def login(request: HttpRequest) -> HttpResponse:
    context: dict[str, Any] = {}
    if request.method == "POST":
        print(request.POST)
    return render(request, "base/login.html", context)