from django.shortcuts import HttpResponse, render

# Create your views here.

def landing(request) -> HttpResponse:
    return render(request, "base/landing.html")

def register(request) -> HttpResponse:
    if request.method == "POST":
        print(request.POST.get("first_name"))
        print(request.POST.get("last_name"))
        print(request.POST.get("email"))
        print(request.POST.get("password1"))
    return render(request, "base/register.html")

def login(request) -> HttpResponse:
    return render(request, "base/login.html")
