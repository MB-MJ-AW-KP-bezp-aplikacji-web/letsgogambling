from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.safestring import mark_safe

from random import randint
from typing import List, Tuple
from copy import deepcopy

REELS = [
    ["🍒", "🍒", "🍒", "🍒", "🍒", "🍇", "🍇", "🍇", "🍇", "🍊", "🍊", "🍊", "🍉", "🍉", "🍉", "💕", "💕", "💕", "🔔", "🔔", "⭐", "⭐", "💎", "7️⃣"],
    ["🍒", "🍒", "🍒", "🍒", "🍇", "🍇", "🍇", "🍇", "🍊", "🍊", "🍊", "🍊", "🍉", "🍉", "🍉", "💕", "💕", "💕", "🔔", "🔔", "⭐", "⭐", "💎", "7️⃣"],
    ["🍒", "🍒", "🍒", "🍒", "🍇", "🍇", "🍇", "🍇", "🍊", "🍊", "🍊", "🍊", "🍉", "🍉", "🍉", "🍉", "💕", "💕", "💕", "🔔", "🔔", "⭐", "💎", "7️⃣"],
]
# REELS = [
#     ["🍒", "🍒", "🍒"],
#     ["🍒", "🍒", "🍒"],
#     ["🍒", "🍒", "🍒"]
# ]
SYMBOL_VALUES = {
        "🍒": 10,
        "🍇": 20,
        "🍊": 30,
        "🍉": 40,
        "💕": 50,
        "🔔": 300,
        "⭐": 400,
        "💎": 500,
        "7️⃣": 1000,
}

@login_required(login_url='/login/')
def slots(request):
    user = request.user
    bet = request.session.get("bet")
    machine = [[ "❓" for _ in range(3)] for _ in range(3)]
    miner_data = {
        "balance": user.balance,
        "machine": machine,
        "last_bet": bet if bet is not None else 10
    }
    return render(request, "casino/slots/index.html", miner_data)

def simulate_spin() -> List[List[str]]:
    machine = []
    for reel in REELS:
        middle = randint(0, len(reel)-1)
        collumn = [reel[(middle - 1) % len(reel)],
               reel[middle],
               reel[(middle + 1) % len(reel)]
        ]
        machine.append(collumn)
    # print(machine)
    return [list(row) for row in zip(*machine)]

def strikethrough(symbol: str) -> str:
    return mark_safe(f"<s>{symbol}</s>")

def check_win(machine: List[List[str]], bet: int) -> Tuple[List[List[str]], int]:
    value = 0
    add_value = lambda i: bet * SYMBOL_VALUES[machine[i][1]]
    print(machine)
    machine_cpy = deepcopy(machine)
    for i in range(3):
        if len(set(machine[i])) == 1:
            value += add_value(i)
            for j in range(3):
                machine_cpy[i][j] = strikethrough(machine_cpy[i][j])
    if machine[0][0] == machine[1][1] == machine[2][2]:
        value += add_value(1)
        for j in range(3):
            machine_cpy[j][j] = strikethrough(machine_cpy[j][j])
    if machine[0][2] == machine[1][1] == machine[2][0]:
        value += add_value(1)
        for j in range(3):
            machine_cpy[j][j+2%2] = strikethrough(machine_cpy[j][j+2%2])
    return machine_cpy, value

# if __name__ == "__main__":
#     print(check_win(simulate_spin(), 10))

@login_required(login_url='/login/')
def spin(request):
    result = None
    machine = None
    err = None
    win = None
    user = request.user
    if request.method == "POST":
        quantity = 0
        try:
            quantity = int(request.POST.get("quantity"))
        except Exception:
            err = "Invalid Amount"
        if err is None:
            request.session["bet"] = quantity
            if quantity > user.balance or user.balance <= 0:
                result = 2
            if result != 2:
                machine = simulate_spin()
                machine, win = check_win(machine, quantity)
                if win > 0:
                    result = 1
                    user.balance += win
                else:
                    result = 0
                    user.balance -= quantity
                user.save()
    bet = request.session.get("bet")
    miner_data = {
        "balance": user.balance,
        "machine": None,
        "result": result,
        "error": err,
        "win": win,
        "last_bet": bet if bet is not None else 10
    }
    if machine is None:
        miner_data["machine"] = [[ "❓" for _ in range(3)] for _ in range(3)]
    else:
        miner_data["machine"] = machine
    return render(request, "casino/slots/index.html", miner_data)