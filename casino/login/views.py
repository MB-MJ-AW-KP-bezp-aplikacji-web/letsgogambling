from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from casino.login.models import User
from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse


def login_page(request):
    err = request.GET.get('e')
    return render(request, "casino/login/index.html",{'error': err})

def login_user(request):
    next = request.GET.get('next')
    if not next or next =='':
        next = '/'
    username = request.POST["username"]
    password = request.POST["password"]
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect(next)
    return redirect(f"{reverse("login_page")}?e=True")

def register_user(request):
    username = request.POST["username"]
    password = request.POST["password"]
    password2 = request.POST["password_rep"]
    if password != password2 or not username  or not password:
        return redirect(f"{reverse("login_page")}?e=True")
    User.objects.create_user(username, password) # type: ignore
    return redirect("login_page")

def logout_user(request):
    logout(request)
    return redirect("login_page")