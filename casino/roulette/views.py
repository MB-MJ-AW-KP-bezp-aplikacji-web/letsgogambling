from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import GameRound, Bet
from .game_logic import WHEEL_CONFIG, get_color_probabilities


@login_required(login_url='/login/')
def roulette(request):
    user = request.user

    current_round = GameRound.objects.filter(
        status__in=['BETTING', 'SPINNING']
    ).order_by('-round_number').first()

    recent_bets = Bet.objects.filter(user=user).select_related('round')[:10]

    from casino.base.models import History
    total_winnings = sum(
        h.amount for h in History.objects.filter(u_id=user)
    )

    context = {
        'balance': user.balance,
        'username': user.username,
        'current_round': current_round,
        'recent_bets': recent_bets,
        'total_winnings': total_winnings,
        'wheel_config': WHEEL_CONFIG,
        'color_probabilities': get_color_probabilities(),
    }

    return render(request, "casino/roulette/index.html", context)
