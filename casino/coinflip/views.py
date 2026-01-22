from secrets import choice
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db import transaction
from casino.login.models import User
from casino.utils.balance_tracker import update_balance


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

            # Use transaction with row-level locking to prevent race conditions
            with transaction.atomic():
                # Lock the user row for update
                locked_user = User.objects.select_for_update().get(pk=user.pk)

                if quantity > locked_user.balance or locked_user.balance <= 0:
                    result = 2
                if result != 2:
                    rand = choice([0, 1])
                    if rand == usr_choice:
                        result = 1
                        update_balance(locked_user, quantity, f"coinflip_win_{quantity}")
                    else:
                        result = 0
                        update_balance(locked_user, -quantity, f"coinflip_loss_{quantity}")

            # Refresh user to get updated balance after transaction
            user.refresh_from_db()

    bet = request.session.get("bet")
    return render(request, "casino/coinflip/index.html",
                  {"balance": user.balance, "result": result, "error": err, "last_bet": bet if bet is not None else 10,
                   "last_choice": request.session.get("choice")})
