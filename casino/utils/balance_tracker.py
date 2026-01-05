"""
Utility for tracking balance changes with reasons.
"""
import logging
from auditlog.context import set_actor
from auditlog.models import LogEntry
from django.db.models.signals import pre_save
from django.dispatch import receiver
import threading

logger = logging.getLogger('auditlog')

# Thread-local storage for balance change reasons
_thread_locals = threading.local()


def log_balance_change(user, old_balance, new_balance, reason, actor=None):
    """
    Log a balance change with context about why it happened.

    Args:
        user: The User whose balance changed
        old_balance: Balance before change
        new_balance: Balance after change
        reason: Why the balance changed (e.g., 'mining_payout', 'debug_add', 'bet_win', 'bet_loss', 'code_redeem')
        actor: Who triggered the change (optional, defaults to the user themselves)
    """
    amount = new_balance - old_balance
    actor_name = actor.username if actor else user.username

    # Format amount with sign, handling both int and float
    amount_str = f"+{amount}" if amount >= 0 else str(amount)

    logger.info(
        f"[BALANCE] {user.username}: {old_balance} → {new_balance} "
        f"({amount_str}) | Reason: {reason} | By: {actor_name}"
    )


def update_balance(user, amount, reason, actor=None, save=True):
    """
    Update a user's balance and log the reason.

    Args:
        user: The User object
        amount: Amount to add (can be negative)
        reason: Why the balance is changing
        actor: Who triggered the change (optional)
        save: Whether to save the user object (default: True)

    Returns:
        The new balance
    """
    old_balance = user.balance
    user.balance += amount

    # Store reason in thread-local storage before save
    _thread_locals.balance_change_reason = reason
    _thread_locals.balance_change_user_id = user.pk

    if save:
        try:
            if actor:
                with set_actor(actor):
                    user.save()
            else:
                user.save()
        finally:
            # Clean up thread-local storage
            _thread_locals.balance_change_reason = None
            _thread_locals.balance_change_user_id = None

    # Log to stdout
    log_balance_change(user, old_balance, user.balance, reason, actor)

    return user.balance


# Signal handler to add reason to audit log at creation time
@receiver(pre_save, sender=LogEntry)
def add_balance_change_reason(sender, instance, **kwargs):
    """Add balance change reason to audit log entry when it's created."""
    # Only process if this is a new log entry and we have a reason stored
    if not instance.pk and hasattr(_thread_locals, 'balance_change_reason'):
        reason = _thread_locals.balance_change_reason
        user_id = getattr(_thread_locals, 'balance_change_user_id', None)

        # Check if this log entry is for the user we're tracking
        if reason and user_id and str(instance.object_id) == str(user_id):
            # Check if balance field changed
            if instance.changes and 'balance' in instance.changes_dict:
                # Convert balance values to numbers for calculation
                try:
                    old_val = float(instance.changes_dict['balance'][0]) if instance.changes_dict['balance'][0] else 0
                    new_val = float(instance.changes_dict['balance'][1]) if instance.changes_dict['balance'][1] else 0
                    amount = new_val - old_val
                except (ValueError, TypeError):
                    amount = 0

                instance.additional_data = {
                    'balance_change_reason': reason,
                    'amount': str(amount)
                }
