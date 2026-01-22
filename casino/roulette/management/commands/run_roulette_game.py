"""
Django management command to run the automatic roulette game loop.

This command should run continuously in the background (separate process).
It creates new rounds every 10 seconds and broadcasts events to all players.

Run with: python manage.py run_roulette_game
"""

import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from casino.roulette.models import GameRound, Bet
from casino.roulette.game_logic import spin_wheel, calculate_payout
from casino.base.models import History
from casino.utils.balance_tracker import update_balance


class Command(BaseCommand):
    help = 'Runs the automatic roulette game loop'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting roulette game loop...'))

        # Initialize channel layer for WebSocket broadcasts
        self.channel_layer = get_channel_layer()

        # Initialize round counter
        last_round = GameRound.objects.order_by('-round_number').first()
        self.current_round_number = last_round.round_number + 1 if last_round else 1

        # Main game loop
        while True:
            try:
                self.run_game_round()
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nShutting down game loop...'))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error in game loop: {e}'))
                time.sleep(1)  # Brief pause before retrying

    # Timing constants (in seconds)
    BETTING_TIME = 15
    SPIN_ANIMATION_TIME = 3

    def run_game_round(self):
        """Execute a single game round"""

        # Phase 1: Create new round (BETTING phase)
        try:
            round_obj = self.create_new_round()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'roulette game already running: {e}'))
            exit(0)
        self.stdout.write(f'Round {round_obj.round_number} - BETTING phase started')

        # Broadcast round start with correct betting time
        self.broadcast_message('round_starting_broadcast', {
            'round_number': round_obj.round_number,
            'time_remaining': self.BETTING_TIME,
        })

        # Wait for betting phase
        time.sleep(self.BETTING_TIME)

        # Phase 2: Lock bets and spin (SPINNING phase)
        round_obj.status = 'SPINNING'
        round_obj.spin_time = timezone.now()
        round_obj.save()

        # Spin the wheel first to get result
        winning_color, winning_slot = spin_wheel()
        round_obj.winning_color = winning_color
        round_obj.winning_slot = winning_slot
        round_obj.save()

        self.stdout.write(f'Round {round_obj.round_number} - SPINNING: {winning_color} (slot {winning_slot})')

        # Broadcast spin with result so client can animate to correct position
        self.broadcast_message('round_spinning_broadcast', {
            'round_number': round_obj.round_number,
            'winning_color': winning_color,
            'winning_slot': winning_slot,
        })

        # Wait for client animation to complete
        time.sleep(self.SPIN_ANIMATION_TIME)

        # Phase 3: Process results and payouts
        self.process_payouts(round_obj, winning_color)

        round_obj.status = 'COMPLETED'
        round_obj.save()

        # Broadcast results
        self.broadcast_message('round_result_broadcast', {
            'round_number': round_obj.round_number,
            'winning_color': winning_color,
            'winning_slot': winning_slot,
        })

        self.stdout.write(self.style.SUCCESS(f'Round {round_obj.round_number} - COMPLETED'))

        # Increment for next round
        self.current_round_number += 1

    def create_new_round(self):
        """Create a new GameRound in BETTING status"""
        return GameRound.objects.create(
            round_number=self.current_round_number,
            status='BETTING',
        )

    def process_payouts(self, round_obj, winning_color):
        """Calculate and distribute payouts for all bets in the round"""
        bets = Bet.objects.filter(round=round_obj).select_related('user')

        winners_count = 0
        total_payout = 0

        for bet in bets:
            payout = calculate_payout(bet.amount, bet.color, winning_color)
            bet.payout = payout
            bet.save()

            if payout > 0:
                # User won - add to balance with tracking
                update_balance(
                    bet.user,
                    payout,
                    f"roulette_win_round_{round_obj.round_number}_{winning_color}"
                )

                # Log in history
                History.objects.create(
                    u_id=bet.user,
                    amount=payout,
                    cashout_time=timezone.now()
                )

                winners_count += 1
                total_payout += payout

                self.stdout.write(
                    f'  Winner: {bet.user.username} won ${payout:.2f} on {bet.color}'
                )

        total_bets = bets.count()
        self.stdout.write(f'  Processed {total_bets} bets, {winners_count} winners, total payout: ${total_payout:.2f}')

    def broadcast_message(self, message_type, data):
        """Send message to all WebSocket clients in the roulette room"""
        async_to_sync(self.channel_layer.group_send)(
            'roulette_game',
            {
                'type': message_type,
                **data
            }
        )
