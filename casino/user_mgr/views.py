from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required(login_url='/login/')
def profile_page(request):
    user = request.user
    ##### placeholder
    miner_data = {
        "balance": user.balance,
        ##### more info
    }
    return render(request, "casino/user_mgr/index.html", miner_data)

@login_required(login_url='/login/')
def add_money(request):
    user = request.user
    zeros_list = list(range(1, 11))
    payout_table = []
    for zeros in zeros_list:
        payout = 40 ** (zeros - 4)
        payout_table.append((zeros, payout))
    miner_data = {
        "balance": user.balance,
        "zeros_list": zeros_list,
        "payout_table": payout_table
        ##### more info
    }
    return render(request, "casino/user_mgr/add_money.html", miner_data)

# Create your views here.
@login_required(login_url='/login/')
def magic_money_button(request):
    user = request.user
    if request.method == "POST":
        user.balance += 100
        user.save()
        messages.success(request, "Updated balance! +$100")
        return redirect('add_money')
    messages.error(request, "Donation error")
    return redirect('add_money')

@login_required(login_url='/login/')
def challenge(request):
    user = request.user
    if request.method == "POST":
        amount = int(request.POST["quantity"])
        return redirect('add_money')
    return redirect('add_money')