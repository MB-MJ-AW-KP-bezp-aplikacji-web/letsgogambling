import base64
import hashlib
from secrets import choice
import string

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from casino.base.models import History
from casino.settings import DEBUG
from django.http import Http404

def make_challenge():
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(choice(alphabet) for _ in range(24))



@login_required(login_url='/login/')
def profile_page(request):
    user = request.user
    wins = History.objects.filter(u_id=user).order_by('-cashout_time')
    ##### placeholder
    miner_data = {
        "balance": user.balance,
        "wins": wins
        ##### more info
    }
    return render(request, "casino/user_mgr/index.html", miner_data)

MIN_ZEROS = 6
@login_required(login_url='/login/')
def add_money(request):
    user = request.user
    chal = request.session.get("chal")
    err = None
    if chal is None:
        request.session["chal"] = chal = make_challenge()
    zeros_list = list(range(0, 11))
    payout_table = []
    for zeros in zeros_list:
        payout = 256 ** (zeros - MIN_ZEROS)
        payout_table.append((zeros, payout))
    pay = None
    while True: # fake goto
        if request.method == "POST":
            sufix = request.POST.get("sufix")
            if sufix is None:
                err = "Invalid Sufix"
                break
            fr_sufix = ''
            try:
                fr_sufix = base64.b64decode(sufix.encode()).decode()
            except Exception:
                err = "Invalid Sufix"
                break
            result = hashlib.sha256(f"{chal}{fr_sufix}".encode()).hexdigest()
            zeros = len(result) - len(result.lstrip('0'))

            if zeros < MIN_ZEROS:
                err = "Not enough leading zeros in hash"
                break
            pay = payout_table[zeros][1]
            user.balance += pay
            user.save()
            request.session["chal"] = chal = make_challenge()
        break
    miner_data = {
        "balance": user.balance,
        "zeros_list": zeros_list,
        "payout_table": payout_table,
        "chal": chal,
        "error": err,
        "payout": pay,
        "debug": DEBUG,
        ##### more info
    }
    return render(request, "casino/user_mgr/add_money.html", miner_data)


# Create your views here.
@login_required(login_url='/login/')
def magic_money_button(request):
    if not DEBUG:
        raise Http404("Page not found")

    user = request.user
    if request.method == "POST":
        user.balance += 100
        user.save()
        messages.success(request, "Updated balance! +$100")
        return redirect('add_money')
    messages.error(request, "Donation error")
    return redirect('add_money')

