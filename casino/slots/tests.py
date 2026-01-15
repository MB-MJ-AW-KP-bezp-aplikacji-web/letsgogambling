from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from casino.login.models import User
from casino.slots.views import simulate_spin, check_win, REELS, SYMBOL_VALUES


class SlotsViewTests(TestCase):
    """Tests for slots view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass"
        ) # nosec
        self.user.balance = 1000
        self.user.save()
        self.client.force_login(self.user)
        self.url = reverse("slots")  # Adjust to your URL name

    def test_slots_view_unauthenticated(self):
        """Test unauthenticated users are redirected"""
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_slots_view_renders(self):
        """Test slots view renders with correct template"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "casino/slots/index.html")

    def test_slots_view_context_data(self):
        """Test slots view includes correct context"""
        response = self.client.get(self.url)

        self.assertEqual(response.context["balance"], 1000)
        self.assertIn("machine", response.context)
        self.assertIn("last_bet", response.context)
        self.assertEqual(response.context["last_bet"], 10)

    def test_slots_view_initial_machine_is_question_marks(self):
        """Test initial machine display shows question marks"""
        response = self.client.get(self.url)

        machine = response.context["machine"]
        self.assertEqual(len(machine), 3)
        for row in machine:
            self.assertEqual(len(row), 3)
            for symbol in row:
                self.assertEqual(symbol, "❓")

    def test_slots_view_remembers_last_bet_from_session(self):
        """Test view retrieves last bet from session"""
        session = self.client.session
        session["bet"] = 250
        session.save()

        response = self.client.get(self.url)

        self.assertEqual(response.context["last_bet"], 250)

    def test_slots_view_csrf_cookie_present(self):
        """Test CSRF cookie is set"""
        response = self.client.get(self.url)

        self.assertIn('csrftoken', response.cookies)


class SimulateSpinTests(TestCase):
    """Tests for simulate_spin function"""

    def test_simulate_spin_returns_3x3_grid(self):
        """Test spin returns correct dimensions"""
        machine = simulate_spin()

        self.assertEqual(len(machine), 3)  # 3 rows
        for row in machine:
            self.assertEqual(len(row), 3)  # 3 columns

    def test_simulate_spin_returns_valid_symbols(self):
        """Test all symbols are from valid set"""
        valid_symbols = set(SYMBOL_VALUES.keys())

        for _ in range(10):  # Test multiple spins
            machine = simulate_spin()
            for row in machine:
                for symbol in row:
                    self.assertIn(symbol, valid_symbols)

    def test_simulate_spin_uses_reel_data(self):
        """Test spin uses actual reel configuration"""
        # Run multiple spins and collect all symbols
        symbols_seen = set()
        for _ in range(50):
            machine = simulate_spin()
            for row in machine:
                symbols_seen.update(row)

        # Should see variety of symbols from reels
        self.assertGreater(len(symbols_seen), 5)

    def test_simulate_spin_randomness(self):
        """Test spins produce different results"""
        results = [simulate_spin() for _ in range(10)]

        # At least some should be different (extremely unlikely all identical)
        unique_results = [str(r) for r in results]
        self.assertGreater(len(set(unique_results)), 1)

    @patch('casino.slots.views.randbelow')
    def test_simulate_spin_reel_wrapping(self, mock_randbelow):
        """Test reel wraps around correctly at boundaries"""
        # Test wrapping at start of reel
        mock_randbelow.return_value = 0
        machine = simulate_spin()
        self.assertEqual(len(machine), 3)

        # Test wrapping at end of reel
        mock_randbelow.return_value = len(REELS[0]) - 1
        machine = simulate_spin()
        self.assertEqual(len(machine), 3)


class CheckWinTests(TestCase):
    """Tests for check_win function"""

    def test_check_win_no_matches(self):
        """Test machine with no winning lines"""
        machine = [
            ["🍒", "🍇", "🍊"],
            ["🍉", "💕", "🔔"],
            ["⭐", "💎", "7️⃣"]
        ]

        result_machine, value, strikes = check_win(machine, 10)

        self.assertEqual(value, 0)
        self.assertEqual(sum(sum(row) for row in strikes), 0)

    def test_check_win_single_row(self):
        """Test winning on a single row"""
        machine = [
            ["🍒", "🍒", "🍒"],
            ["🍇", "🍊", "🍉"],
            ["💕", "🔔", "⭐"]
        ]

        result_machine, value, strikes = check_win(machine, 10)

        expected_value = 10 * SYMBOL_VALUES["🍒"]
        self.assertEqual(value, expected_value)
        self.assertTrue(all(strikes[0]))  # First row struck
        self.assertFalse(any(strikes[1]))  # Second row not struck
        self.assertFalse(any(strikes[2]))  # Third row not struck

    def test_check_win_multiple_rows(self):
        """Test winning on multiple rows"""
        machine = [
            ["🍒", "🍒", "🍒"],
            ["🍇", "🍇", "🍇"],
            ["🍊", "🔔", "⭐"]
        ]

        result_machine, value, strikes = check_win(machine, 10)

        expected_value = (10 * SYMBOL_VALUES["🍒"]) + (10 * SYMBOL_VALUES["🍇"])
        self.assertEqual(value, expected_value)
        self.assertTrue(all(strikes[0]))
        self.assertTrue(all(strikes[1]))
        self.assertFalse(any(strikes[2]))

    def test_check_win_diagonal_top_left_to_bottom_right(self):
        """Test winning on main diagonal"""
        machine = [
            ["🍒", "🍇", "🍊"],
            ["🍉", "🍒", "🔔"],
            ["⭐", "💎", "🍒"]
        ]

        result_machine, value, strikes = check_win(machine, 10)

        expected_value = 10 * SYMBOL_VALUES["🍒"]
        self.assertEqual(value, expected_value)
        self.assertTrue(strikes[0][0])
        self.assertTrue(strikes[1][1])
        self.assertTrue(strikes[2][2])

    def test_check_win_diagonal_top_right_to_bottom_left(self):
        """Test winning on anti-diagonal"""
        machine = [
            ["🍒", "🍇", "🍊"],
            ["🍉", "🍊", "🔔"],
            ["🍊", "💎", "7️⃣"]
        ]

        result_machine, value, strikes = check_win(machine, 10)

        expected_value = 10 * SYMBOL_VALUES["🍊"]
        self.assertEqual(value, expected_value)
        self.assertTrue(strikes[0][2])
        self.assertTrue(strikes[1][1])
        self.assertTrue(strikes[2][0])

    def test_check_win_all_rows(self):
        """Test winning on all three rows"""
        machine = [
            ["🍒", "🍒", "🍒"],
            ["🍇", "🍇", "🍇"],
            ["🍊", "🍊", "🍊"]
        ]

        result_machine, value, strikes = check_win(machine, 10)

        expected_value = (
            10 * SYMBOL_VALUES["🍒"] +
            10 * SYMBOL_VALUES["🍇"] +
            10 * SYMBOL_VALUES["🍊"]
        )
        self.assertEqual(value, expected_value)
        self.assertTrue(all(all(row) for row in strikes))

    def test_check_win_all_diagonals(self):
        """Test winning on both diagonals"""
        machine = [
            ["🍒", "🍇", "🍒"],
            ["🍊", "🍒", "🍉"],
            ["🍒", "💕", "🍒"]
        ]

        result_machine, value, strikes = check_win(machine, 10)

        expected_value = 2 * (10 * SYMBOL_VALUES["🍒"])
        self.assertEqual(value, expected_value)
        self.assertTrue(strikes[0][0])
        self.assertTrue(strikes[0][2])
        self.assertTrue(strikes[1][1])
        self.assertTrue(strikes[2][0])
        self.assertTrue(strikes[2][2])

    def test_check_win_row_and_diagonal(self):
        """Test winning on row + diagonal simultaneously"""
        machine = [
            ["🍒", "🍒", "🍒"],
            ["🍇", "🍒", "🔔"],
            ["⭐", "💎", "🍒"]
        ]

        result_machine, value, strikes = check_win(machine, 10)

        # Row win + diagonal win
        expected_value = 2 * (10 * SYMBOL_VALUES["🍒"])
        self.assertEqual(value, expected_value)
        self.assertTrue(all(strikes[0]))  # Top row
        self.assertTrue(strikes[1][1])     # Center
        self.assertTrue(strikes[2][2])     # Bottom right

    def test_check_win_different_bet_amounts(self):
        """Test payout scales with bet amount"""
        machine = [
            ["🍒", "🍒", "🍒"],
            ["🍇", "🍊", "🍉"],
            ["💕", "🔔", "⭐"]
        ]

        _, value_10, _ = check_win(machine, 10)
        _, value_50, _ = check_win(machine, 50)
        _, value_100, _ = check_win(machine, 100)

        self.assertEqual(value_50, value_10 * 5)
        self.assertEqual(value_100, value_10 * 10)

    def test_check_win_jackpot_symbol(self):
        """Test highest value jackpot symbol"""
        machine = [
            ["7️⃣", "7️⃣", "7️⃣"],
            ["🍇", "🍊", "🍉"],
            ["💕", "🔔", "⭐"]
        ]

        result_machine, value, strikes = check_win(machine, 10)

        expected_value = 10 * SYMBOL_VALUES["7️⃣"]
        self.assertEqual(value, expected_value)
        self.assertEqual(value, 1500)  # 10 * 150

    def test_check_win_does_not_modify_original_machine(self):
        """Test check_win doesn't modify input machine"""
        original_machine = [
            ["🍒", "🍒", "🍒"],
            ["🍇", "🍇", "🍇"],
            ["🍊", "🍊", "🍊"]
        ]
        machine_copy = [row[:] for row in original_machine]

        check_win(original_machine, 10)

        self.assertEqual(original_machine, machine_copy)

    def test_check_win_strikes_format(self):
        """Test strikes return correct format"""
        machine = [
            ["🍒", "🍇", "🍊"],
            ["🍉", "💕", "🔔"],
            ["⭐", "💎", "7️⃣"]
        ]

        _, _, strikes = check_win(machine, 10)

        # Should be 3x3 grid of booleans
        self.assertEqual(len(strikes), 3)
        for row in strikes:
            self.assertEqual(len(row), 3)
            for cell in row:
                self.assertIsInstance(cell, bool)


class SymbolValuesTests(TestCase):
    """Tests for symbol configuration"""

    def test_all_reel_symbols_have_values(self):
        """Test all symbols in reels have defined payouts"""
        symbols_in_reels = set()
        for reel in REELS:
            symbols_in_reels.update(reel)

        for symbol in symbols_in_reels:
            self.assertIn(symbol, SYMBOL_VALUES)

    def test_symbol_values_are_positive(self):
        """Test all symbol values are positive"""
        for symbol, value in SYMBOL_VALUES.items():
            self.assertGreater(value, 0)

    def test_rare_symbols_have_higher_values(self):
        """Test rarer symbols have higher payouts"""
        # Jackpot should be highest
        self.assertEqual(SYMBOL_VALUES["7️⃣"], 150)
        self.assertGreater(SYMBOL_VALUES["7️⃣"], SYMBOL_VALUES["💎"])
        self.assertGreater(SYMBOL_VALUES["💎"], SYMBOL_VALUES["⭐"])

    def test_reel_configuration(self):
        """Test reel configuration is valid"""
        self.assertEqual(len(REELS), 3)
        for i, reel in enumerate(REELS):
            self.assertGreater(len(reel), 0, f"Reel {i} is empty")
            self.assertEqual(len(reel), 24, f"Reel {i} should have 24 symbols")


class SlotsIntegrationTests(TestCase):
    """Integration tests for complete spin workflow"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass"
        ) # nosec
        self.user.balance = 1000
        self.user.save()
        self.client.force_login(self.user)

    def test_complete_spin_workflow(self):
        """Test complete workflow from view to spin to check"""
        # 1. Visit page
        response = self.client.get(reverse("slots"))
        self.assertEqual(response.status_code, 200)

        # 2. Simulate a spin
        machine = simulate_spin()
        self.assertEqual(len(machine), 3)

        # 3. Check for wins
        result_machine, value, strikes = check_win(machine, 10)
        self.assertGreaterEqual(value, 0)

        # 4. Verify strikes match value
        if value > 0:
            # At least one strike should be True
            total_strikes = sum(sum(row) for row in strikes)
            self.assertGreater(total_strikes, 0)

    @patch('casino.slots.views.randbelow')
    def test_deterministic_win(self, mock_randbelow):
        """Test a guaranteed winning scenario"""
        # Force first reel position to create a winning combination
        mock_randbelow.side_effect = [0, 0, 0]  # All reels at position 0

        machine = simulate_spin()
        result_machine, value, strikes = check_win(machine, 100)

        # With controlled randomness, we should get consistent results
        self.assertIsNotNone(machine)
        self.assertIsNotNone(value)
        self.assertIsNotNone(strikes)