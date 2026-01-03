from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from casino.login.models import User
from django.shortcuts import render, redirect


def login_page(request):
    err = request.session.get('error')
    if request.user.is_authenticated:
        return redirect('/')
    request.session['legit'] = False
    if request.method == "POST":
        if not request.POST.get('pin'):
            return render(request, "casino/login/index.html", {'error': "Empty PIN"})
        pin = int(request.POST.get('pin'))
        if pin == 213721372137:
            request.session['legit'] = True
            request.session['error'] = None
            return redirect('register')
    return render(request, "casino/login/index.html", {'error': err})


def login_user(request):
    next = request.GET.get('next')
    if not next or next == '':
        next = '/'
    username = request.POST["username"]
    password = request.POST["password"]
    user = authenticate(request, username=username, password=password)
    if user is not None:
        request.session['error'] = None
        login(request, user)
        return redirect(next)
    request.session['error'] = 'Invalid username and/or password.'
    return redirect('login_page')


def register_user(request):
    if not request.session.get('legit'):
        return redirect('login_page')
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        password2 = request.POST["password_rep"]
        if password != password2 or not username or not password:
            request.session['error'] = "passwords don't match"
            return redirect('register')
        if User.objects.filter(username=username).exists():
            request.session['error'] = "user with this username already exists."
            return redirect('register')
        try:
            validate_password(password, user=None)
        except ValidationError as e:
            request.session['error'] = ' \n'.join(e.messages)
            return redirect('register')

        user = User.objects.create_user(username, password)
        login(request, user)
        request.session['error'] = None
        return redirect("/")
    return render(request, "casino/login/register.html", {'error': request.session.get('error')})


def logout_user(request):
    logout(request)
    return redirect("login_page")
