
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from casino.base.models import User, History
from casino.slots.views import simulate_spin, check_win
from casino.api.serializers import (
    BalanceResponseSerializer,
    SpinRequestSerializer,
    SpinResponseSerializer,
    CoinflipRequestSerializer,
    CoinflipResponseSerializer
)
from secrets import choice

@extend_schema(
    responses=BalanceResponseSerializer,
    description="Get current user balance"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_balance(request):
    user = request.user
    return Response({"balance": user.balance})

@extend_schema(
    request=SpinRequestSerializer,
    responses=SpinResponseSerializer,
    description="Spin the slot machine. Bet amount is per spin, count is number of spins (1-5)."
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def spin_api(request):
    raw_bet = request.data.get("bet")
    raw_count = request.data.get("count", 1)

    try:
        bet = int(raw_bet)
        count = int(raw_count)
    except (TypeError, ValueError):
        return Response({"error": "Bet must be a number."}, status=400)

    if bet <= 0:
        return Response({"error": "Invalid bet"}, status=400)

    if count < 1 or count > 5:
        return Response({"error": "Count must be between 1 and 5"}, status=400)

    total_bet = bet * count

    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=request.user.pk)

        if total_bet > user.balance:
            return Response({
                "results": [],
                "balance": user.balance,
                "total_win": 0,
                "error": "Insufficient balance"
            })

        # Deduct total bet first (atomic)
        user.balance -= total_bet

        results = []
        total_win = 0

        for _ in range(count):
            machine = simulate_spin()
            machine, win, strikes = check_win(machine, bet)

            if win > 0:
                total_win += win
                results.append({
                    "machine": machine,
                    "strikes": strikes,
                    "win": win,
                    "result": 1
                })
            else:
                results.append({
                    "machine": machine,
                    "strikes": strikes,
                    "win": 0,
                    "result": 0
                })

        # Add total winnings
        user.balance += total_win

        if total_win > 0:
            history_entry = History(u_id=user, amount=total_win, cashout_time=timezone.now())
            history_entry.save()

        user.save()

    return Response({
        "results": results,
        "balance": user.balance,
        "total_win": total_win
    })

@extend_schema(
    request=CoinflipRequestSerializer,
    responses=CoinflipResponseSerializer,
    description="Flip a coin. Choice: 0 or 1. Win doubles your bet."
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def coinflip_api(request):
    raw_bet = request.data.get("bet")
    raw_choice = request.data.get("choice")

    try:
        bet = int(raw_bet)
        usr_choice = int(raw_choice)
    except (TypeError, ValueError):
        return Response({"error": "Invalid bet or choice."}, status=400)

    if bet <= 0:
        return Response({"error": "Invalid bet"}, status=400)

    if usr_choice not in [0, 1]:
        return Response({"error": "Invalid choice"}, status=400)

    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=request.user.pk)

        if bet > user.balance:
            return Response({
                "result": 2,
                "balance": user.balance,
                "win": 0,
                "flip_result": None
            })

        # Deduct bet first (atomic)
        user.balance -= bet

        flip_result = choice([0, 1])
        if flip_result == usr_choice:
            user.balance += bet * 2  # Return bet + win
            result = 1
            win = bet
            history_entry = History(u_id=user, amount=win, cashout_time=timezone.now())
            history_entry.save()
        else:
            result = 0
            win = 0

        user.save()

    return Response({
        "result": result,
        "balance": user.balance,
        "win": win,
        "flip_result": flip_result
    })