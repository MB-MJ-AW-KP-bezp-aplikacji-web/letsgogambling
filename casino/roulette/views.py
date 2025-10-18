import random

from django.contrib.auth.decorators import login_required

from django.shortcuts import render, HttpResponse

from casino.login.models import User


@login_required(login_url='/login/')
def roulette(request):
    result = None
    err = None
    user = request.user
    if request.method == "POST":
        choice = None
        quantity = None
        try:
            choice = int(request.POST.get("choice"))
            quantity = int(request.POST.get("quantity"))
        except Exception:
            err = "Invalid Ammount"
        if err is None:
            if quantity > user.balance or user.balance <= 0:
                result = 2
            if result != 2 :
                rand = random.randint(0, 1)
                if rand == choice:
                    result = 1
                    user.balance += quantity
                else:
                    result = 0
                    user.balance -= quantity
                user.save()
    return render(request, "casino/roulette/index.html", {"balance": user.balance, "result": result, "error": err})
