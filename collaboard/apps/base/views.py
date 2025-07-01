from django.shortcuts import HttpResponse, redirect, render
from django.urls import reverse

# Create your views here.

def landing(request) -> HttpResponse:
    return render(request, "base/landing.html")

def register(request) -> HttpResponse:
    if request.method == "POST":
        # Implement User Creation Logic Now
        # On success add created query parameter
        return redirect(f"{reverse('login')}?created=true")
    return render(request, "base/register.html")

def login(request) -> HttpResponse:
    if request.method == "POST":
        print("POST")
    just_created = request.GET.get("created") == "true"
    return render(request, "base/login.html", {"just_created": just_created})
