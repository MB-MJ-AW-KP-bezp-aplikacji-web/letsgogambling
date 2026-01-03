from django.db import models
from casino.login.models import User


class GameRound(models.Model):
    """Represents a single 10-second roulette round"""

    STATUS_CHOICES = [
        ('BETTING', 'Betting Phase'),
        ('SPINNING', 'Spinning Phase'),
        ('COMPLETED', 'Completed'),
    ]

    COLOR_CHOICES = [
        ('GRAY', 'Gray'),
        ('RED', 'Red'),
        ('BLUE', 'Blue'),
        ('GOLD', 'Gold'),
    ]

    id = models.AutoField(primary_key=True)
    round_number = models.IntegerField(unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='BETTING')
    winning_color = models.CharField(max_length=4, choices=COLOR_CHOICES, null=True, blank=True)
    winning_slot = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    spin_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-round_number']

    def __str__(self):
        return f"Round {self.round_number} - {self.status}"


class Bet(models.Model):
    """Represents an individual player's bet on a color"""

    COLOR_CHOICES = [
        ('GRAY', 'Gray'),
        ('RED', 'Red'),
        ('BLUE', 'Blue'),
        ('GOLD', 'Gold'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roulette_bets')
    round = models.ForeignKey(GameRound, on_delete=models.CASCADE, related_name='bets')
    color = models.CharField(max_length=4, choices=COLOR_CHOICES)
    amount = models.BigIntegerField()
    payout = models.BigIntegerField(default=0)
    placed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-placed_at']
        unique_together = ['user', 'round', 'color']

    def __str__(self):
        return f"{self.user.username} - ${self.amount} on {self.color} (Round {self.round.round_number})"
