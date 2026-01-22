"""
WebSocket consumer for real-time roulette game communication.
Handles player connections, bet placement, and round updates.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.db import transaction
from .models import GameRound, Bet
from casino.utils.balance_tracker import update_balance


class RouletteConsumer(AsyncWebsocketConsumer):
    """
    Handles WebSocket connections for the roulette game.

    Message Types Sent to Client:
        - round_state: Current game round info (on connect + round changes)
        - bet_placed: Notification when any player places a bet
        - round_spinning: Round entering spin phase (2s before result)
        - round_result: Winning color and payouts
        - balance_update: User's balance changed
        - error: Error message

    Message Types Received from Client:
        - place_bet: Player wants to place a bet
        - get_state: Request current game state
    """

    async def connect(self):
        """Handle new WebSocket connection"""
        self.room_group_name = 'roulette_game'

        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        current_round = await self.get_current_round()
        history = await self.get_history()

        if current_round:
            await self.send(text_data=json.dumps({
                'type': 'round_state',
                'round_number': current_round['round_number'],
                'status': current_round['status'],
                'time_remaining': current_round['time_remaining'],
                'total_bets': current_round['total_bets'],
                'history': history,
                'bets': current_round['bets'],
            }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Handle messages from WebSocket client
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'place_bet':
                await self.handle_place_bet(data)
            elif message_type == 'get_state':
                await self.handle_get_state()
            else:
                await self.send_error('Unknown message type')

        except json.JSONDecodeError:
            await self.send_error('Invalid JSON')
        except Exception as e:
            await self.send_error(f'Server error: {str(e)}')

    async def handle_place_bet(self, data):
        """
        Process a bet placement request from a player

        Expected data format:
        {
            'type': 'place_bet',
            'color': 'RED',
            'amount': 100.0
        }
        """
        # Re-verify user is still authenticated (handles logout in other tabs)
        user = await self.get_fresh_user()
        if user is None:
            await self.send_error('Session expired - please refresh the page')
            await self.close()
            return

        color = data.get('color', '').upper()
        amount = data.get('amount')

        if color not in ['GRAY', 'RED', 'BLUE', 'GOLD']:
            await self.send_error('Invalid color')
            return

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            await self.send_error('Invalid bet amount')
            return

        result = await self.place_bet(user, color, amount)

        if result['success']:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'bet_placed_broadcast',
                    'username': user.username,
                    'color': color,
                    'amount': amount,
                    'round_number': result['round_number'],
                }
            )

            await self.send(text_data=json.dumps({
                'type': 'balance_update',
                'balance': result['new_balance'],
            }))
        else:
            await self.send_error(result['error'])

    async def handle_get_state(self):
        """Send current game state to requesting client"""
        current_round = await self.get_current_round()
        history = await self.get_history()

        if current_round:
            await self.send(text_data=json.dumps({
                'type': 'round_state',
                'round_number': current_round['round_number'],
                'status': current_round['status'],
                'time_remaining': current_round['time_remaining'],
                'total_bets': current_round['total_bets'],
                'history': history,
                'bets': current_round['bets'],
            }))

    # Channel layer broadcast handlers
    async def bet_placed_broadcast(self, event):
        """Forward bet_placed event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'bet_placed',
            'username': event['username'],
            'color': event['color'],
            'amount': event['amount'],
            'round_number': event['round_number'],
        }))

    async def round_starting_broadcast(self, event):
        """Forward round_starting event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'round_starting',
            'round_number': event['round_number'],
            'time_remaining': event['time_remaining'],
        }))

    async def round_spinning_broadcast(self, event):
        """Forward round_spinning event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'round_spinning',
            'round_number': event['round_number'],
            'winning_color': event['winning_color'],
            'winning_slot': event['winning_slot'],
        }))

    async def round_result_broadcast(self, event):
        """Forward round_result event to WebSocket"""
        user = self.scope['user']
        user_payout = await self.get_user_payout(user, event['round_number'])

        await self.send(text_data=json.dumps({
            'type': 'round_result',
            'round_number': event['round_number'],
            'winning_color': event['winning_color'],
            'winning_slot': event['winning_slot'],
            'your_payout': user_payout['total_payout'],
            'your_balance': user_payout['new_balance'],
        }))

    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
        }))

    BETTING_TIME = 15

    @database_sync_to_async
    def get_fresh_user(self):
        """
        Re-verify user authentication by checking session validity.
        Returns the user if still authenticated, None otherwise.
        """
        from django.contrib.sessions.models import Session
        from casino.login.models import User

        # Get session key from scope
        session = self.scope.get('session')
        if not session or not session.session_key:
            return None

        try:
            # Check if session still exists in database
            Session.objects.get(session_key=session.session_key)

            # Refresh user from database
            user = self.scope.get('user')
            if user and user.is_authenticated:
                return User.objects.get(pk=user.pk, is_active=True)
        except (Session.DoesNotExist, User.DoesNotExist):
            return None

        return None

    @database_sync_to_async
    def get_current_round(self):
        """Get the current active game round"""
        try:
            round_obj = GameRound.objects.filter(
                status__in=['BETTING', 'SPINNING']
            ).order_by('-round_number').first()

            if not round_obj:
                return None

            now = timezone.now()
            elapsed = (now - round_obj.created_at).total_seconds()
            time_remaining = max(0, self.BETTING_TIME - elapsed)

            total_bets = round_obj.bets.count()

            bets = []
            for bet in round_obj.bets.select_related('user').all():
                bets.append({
                    'username': bet.user.username,
                    'color': bet.color,
                    'amount': bet.amount,
                })

            return {
                'round_number': round_obj.round_number,
                'status': round_obj.status,
                'time_remaining': time_remaining,
                'total_bets': total_bets,
                'bets': bets,
            }
        except Exception:
            return None

    @database_sync_to_async
    def place_bet(self, user, color, amount):
        """
        Place a bet for a user on the current round

        Returns dict with 'success' boolean and additional data
        """
        try:
            # Use transaction with row-level locking to prevent race conditions
            with transaction.atomic():
                # Lock the user row for update to prevent concurrent balance modifications
                from casino.login.models import User
                user = User.objects.select_for_update().get(pk=user.pk)

                round_obj = GameRound.objects.filter(status='BETTING').order_by('-round_number').first()

                if not round_obj:
                    return {'success': False, 'error': 'No active betting round'}

                if user.balance < amount:
                    return {'success': False, 'error': 'Insufficient balance'}

                existing_bet = Bet.objects.filter(
                    user=user,
                    round=round_obj,
                    color=color
                ).first()

                update_balance(
                    user,
                    -amount,
                    f"roulette_bet_round_{round_obj.round_number}_{color}"
                )

                if existing_bet:
                    existing_bet.amount += amount
                    existing_bet.save()
                else:
                    Bet.objects.create(
                        user=user,
                        round=round_obj,
                        color=color,
                        amount=amount,
                    )

                return {
                    'success': True,
                    'round_number': round_obj.round_number,
                    'new_balance': user.balance,
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @database_sync_to_async
    def get_user_payout(self, user, round_number):
        """Get user's total payout for a completed round"""
        try:
            round_obj = GameRound.objects.get(round_number=round_number)
            user_bets = Bet.objects.filter(user=user, round=round_obj)

            total_payout = sum(bet.payout for bet in user_bets)
            user.refresh_from_db()

            return {
                'total_payout': total_payout,
                'new_balance': user.balance,
            }
        except Exception:
            return {
                'total_payout': 0,
                'new_balance': user.balance,
            }

    @database_sync_to_async
    def get_history(self):
        """Get last 10 completed rounds with winning colors"""
        try:
            completed_rounds = GameRound.objects.filter(
                status='COMPLETED',
                winning_color__isnull=False
            ).order_by('-round_number')[:10]

            return [r.winning_color for r in completed_rounds]
        except Exception:
            return []
