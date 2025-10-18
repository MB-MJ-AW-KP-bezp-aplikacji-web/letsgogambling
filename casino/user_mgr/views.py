from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
@login_required(login_url='/login/')
def magic_money_button(request):
    user = request.user
    message = ""
    if request.method == "POST":
        user.balance += 100
        user.save()
        message = "updated balance"

    return render(request, "casino/user_mgr/index.html", {
        "balance": user.balance,
        "message": message
    })

@login_required(login_url='/login/')
def profile_page(request):
    user = request.user
    ##### placeholder
    miner_data = {
        "balance": user.balance,
        ##### more info
    }

    return render(request, "casino/user_mgr/index.html", miner_data)