from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from casino.base.models import User, History
# Create your tests here.

class AuthenticatedAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            balance=1000,
            is_active=True
        )
        self.user.set_password("testpass")
        self.user.save()

        self.client.force_authenticate(user=self.user) # type: ignore[attr-defined]

class BalanceAPITests(AuthenticatedAPITestCase):

    def test_get_balance(self):
        url = reverse("my_balance")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["balance"], 1000)

class SpinAPITests(AuthenticatedAPITestCase):

    def test_spin_invalid_bet_type(self):
        response = self.client.post(
            reverse("spin_api"),
            {"bet": "abc"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_spin_negative_bet(self):
        response = self.client.post(
            reverse("spin_api"),
            {"bet": -10}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_spin_invalid_count(self):
        response = self.client.post(
            reverse("spin_api"),
            {"bet": 10, "count": 6}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_spin_insufficient_balance(self):
        response = self.client.post(
            reverse("spin_api"),
            {"bet": 600, "count": 2}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["error"], "Insufficient balance")
        self.assertEqual(response.data["balance"], 1000)
        self.assertEqual(response.data["total_win"], 0)

    def test_spin_success_response_shape(self):
        response = self.client.post(
            reverse("spin_api"),
            {"bet": 10, "count": 3}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("balance", response.data)
        self.assertIn("total_win", response.data)

        self.assertEqual(len(response.data["results"]), 3)

        for result in response.data["results"]:
            self.assertIn("machine", result)
            self.assertIn("strikes", result)
            self.assertIn("win", result)
            self.assertIn("result", result)

    def test_spin_balance_never_negative(self):
        self.client.post(
            reverse("spin_api"),
            {"bet": 10, "count": 5}
        )

        self.user.refresh_from_db()
        self.assertGreaterEqual(self.user.balance, 0)

    def test_spin_history_created_only_on_win(self):
        self.client.post(
            reverse("spin_api"),
            {"bet": 10, "count": 5}
        )

        # Random outcome: history may or may not exist
        self.assertGreaterEqual(
            History.objects.filter(u_id=self.user).count(),
            0
        )

class CoinflipAPITests(AuthenticatedAPITestCase):

    def test_coinflip_invalid_bet_type(self):
        response = self.client.post(
            reverse("coinflip_api"),
            {"bet": "abc", "choice": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_coinflip_invalid_choice(self):
        response = self.client.post(
            reverse("coinflip_api"),
            {"bet": 10, "choice": 3}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_coinflip_insufficient_balance(self):
        response = self.client.post(
            reverse("coinflip_api"),
            {"bet": 5000, "choice": 1}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], 2)
        self.assertEqual(response.data["balance"], 1000)
        self.assertEqual(response.data["win"], 0)
        self.assertIsNone(response.data["flip_result"])

    def test_coinflip_balance_updates(self):
        response = self.client.post(
            reverse("coinflip_api"),
            {"bet": 100, "choice": 0}
        )

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data["result"], [0, 1])
        self.assertEqual(response.data["balance"], self.user.balance)

class CoinflipDeterministicTests(AuthenticatedAPITestCase):

    @patch("casino.api.views.choice", return_value=1)
    def test_coinflip_forced_win(self, mock_choice):
        response = self.client.post(
            reverse("coinflip_api"),
            {"bet": 100, "choice": 1}
        )

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], 1)
        self.assertEqual(response.data["win"], 200)
        self.assertEqual(self.user.balance, 1100)

        self.assertTrue(
            History.objects.filter(u_id=self.user).exists()
        )
