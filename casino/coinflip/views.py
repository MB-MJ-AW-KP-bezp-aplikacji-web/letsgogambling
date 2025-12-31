from secrets import choice
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required(login_url='/login/')
def coinflip(request):
    result = None
    err = None
    user = request.user
    if request.method == "POST":
        usr_choice = None
        quantity = None
        try:
            usr_choice = int(request.POST.get("choice"))
            quantity = int(request.POST.get("quantity"))
        except Exception:
            err = "Invalid Amount"
        if err is None:
            request.session["bet"] = quantity
            request.session["choice"] = usr_choice
            if quantity > user.balance or user.balance <= 0:
                result = 2
            if result != 2:
                rand = choice([0, 1])
                if rand == usr_choice:
                    result = 1
                    user.balance += quantity
                else:
                    result = 0
                    user.balance -= quantity
                user.save()
    bet = request.session.get("bet")
    return render(request, "casino/coinflip/index.html",
                  {"balance": user.balance, "result": result, "error": err, "last_bet": bet if bet is not None else 10,
                   "last_choice": request.session.get("choice")})
