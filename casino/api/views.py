# from django.shortcuts import render
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics
from casino.base.models import User, History
from casino.slots.views import simulate_spin, check_win
from .serializers import *
# from datetime import datetime

# Create your views here.
@permission_classes([IsAuthenticated])
class ListCreate(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_balance(request):
    user = request.user
    return Response({"balance": user.balance})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def spin_api(request):
    user = request.user
    raw_bet = request.data.get("bet")

    try:
        bet = int(raw_bet)
    except (TypeError, ValueError):
        return Response({"error": "Bet must be a number."}, status=400)


    if bet <= 0:
        return Response({"error": "Invalid bet"}, status=400)

    if bet > user.balance:
        return Response({
            "result": 2,
            "machine": None,
            "balance": user.balance,
            "win": 0
        })

    machine = simulate_spin()
    machine, win, strikes = check_win(machine, bet)

    if win > 0:
        user.balance += win
        result = 1
        history_entry = History(u_id=user, amount=win, cashout_time=timezone.now())
        history_entry.save()
    else:
        user.balance -= bet
        result = 0

    user.save()

    return Response({
        "result": result,
        "machine": machine,
        "strikes": strikes,
        "balance": user.balance,
        "win": win
    })