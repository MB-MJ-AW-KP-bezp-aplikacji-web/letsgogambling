from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.http import url_has_allowed_host_and_scheme

from casino.login.models import User
from django.shortcuts import render, redirect
from casino.settings import REGISTER_PASSWORD


def login_page(request):
    login_err = request.session.get('login_err')
    if request.user.is_authenticated:
        return redirect('/')
    request.session['legit'] = False
    if request.method == "POST":
        if not request.POST.get('pin'):
            return render(request, "casino/login/index.html", {'register_err': "Empty PIN"})
        pin = int(request.POST.get('pin'))
        if pin != REGISTER_PASSWORD:
            return render(request, "casino/login/index.html", {'register_err': "Wrong PIN"})
        else:
            request.session['legit'] = True
            request.session['login_err'] = None
            request.session['register_err'] = None
            return redirect('register')
    return render(request, "casino/login/index.html", {'login_err': login_err})


def login_user(request):
    if request.method != "POST":
        return redirect('login_page')
    next = request.GET.get('next')
    if not next or next == '' or not url_has_allowed_host_and_scheme(next,None):
        next = '/'
    username = request.POST["username"]
    password = request.POST["password"]
    user = authenticate(request, username=username, password=password)
    if user is not None:
        request.session['login_err'] = None
        login(request, user)
        return redirect(next)
    request.session['login_err'] = 'Invalid username and/or password.'
    return redirect('login_page')


def register_user(request):
    if not request.session.get('legit'):
        return redirect('login_page')
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        password2 = request.POST["password_rep"]
        if password != password2 or not username or not password:
            request.session['login_err'] = "passwords don't match"
            return redirect('register')
        if User.objects.filter(username=username).exists():
            request.session['login_err'] = "user with this username already exists."
            return redirect('register')
        try:
            validate_password(password, user=None)
        except ValidationError as e:
            request.session['login_err'] = ' \n'.join(e.messages)
            return redirect('register')

        user = User.objects.create_user(username, password)
        login(request, user)
        request.session['login_err'] = None
        return redirect("/")
    return render(request, "casino/login/register.html", {'login_err': request.session.get('login_err')})


def logout_user(request):
    logout(request)
    return redirect("login_page")
