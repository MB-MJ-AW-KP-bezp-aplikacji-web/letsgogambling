"""
Core game logic for multiplayer roulette.
Handles wheel configuration, random selection, and payout calculation.
"""

import secrets
from typing import Dict, Tuple

# Wheel configuration: 54 total slots
WHEEL_CONFIG = {
    'GRAY': {'slots': 26, 'multiplier': 2.0},
    'RED': {'slots': 17, 'multiplier': 3.0},
    'BLUE': {'slots': 10, 'multiplier': 5.0},
    'GOLD': {'slots': 1, 'multiplier': 50.0},
}

WHEEL = [
    'GOLD', 'BLUE', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY',
    'BLUE', 'GRAY', 'BLUE', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY',
    'BLUE', 'GRAY', 'BLUE', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY',
    'BLUE', 'GRAY', 'BLUE', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY',
    'BLUE', 'GRAY', 'BLUE', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY',
    'BLUE'
]


def spin_wheel() -> Tuple[str, int]:
    """
    Randomly select a winning slot using cryptographically secure randomness.

    Returns:
        Tuple of (winning_color, slot_index)
        Example: ('RED', 32)
    """
    slot_index = secrets.randbelow(54)
    winning_color = WHEEL[slot_index]
    return winning_color, slot_index


def calculate_payout(bet_amount: float, bet_color: str, winning_color: str) -> float:
    """
    Calculate payout for a single bet.

    Args:
        bet_amount: Amount wagered
        bet_color: Color the user bet on
        winning_color: Color that won the spin

    Returns:
        Payout amount (0 if lost, bet_amount * multiplier if won)
    """
    if bet_color != winning_color:
        return 0.0

    multiplier = WHEEL_CONFIG[bet_color]['multiplier']
    return bet_amount * multiplier


def get_color_probabilities() -> Dict[str, float]:
    """
    Calculate probability percentages for each color.
    Useful for displaying odds to players.

    Returns:
        Dictionary mapping color to probability percentage
        Example: {'GRAY': 48.15, 'RED': 31.48, ...}
    """
    return {
        color: (config['slots'] / 54) * 100
        for color, config in WHEEL_CONFIG.items()
    }
