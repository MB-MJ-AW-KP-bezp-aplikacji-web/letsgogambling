from rest_framework import serializers
from casino.base.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "balance"]

# Request Serializers
class SpinRequestSerializer(serializers.Serializer):
    bet = serializers.IntegerField(min_value=1, help_text="Amount to bet per spin")
    count = serializers.IntegerField(min_value=1, max_value=5, default=1, help_text="Number of spins (1-5)")

class CoinflipRequestSerializer(serializers.Serializer):
    bet = serializers.IntegerField(min_value=1, help_text="Amount to bet")
    choice = serializers.IntegerField(min_value=0, max_value=1, help_text="0 or 1")

# Response Serializers
class BalanceResponseSerializer(serializers.Serializer):
    balance = serializers.IntegerField()

class SpinResultItemSerializer(serializers.Serializer):
    machine = serializers.ListField(child=serializers.ListField(child=serializers.CharField()))
    strikes = serializers.ListField(child=serializers.ListField(child=serializers.IntegerField()))
    win = serializers.IntegerField()
    result = serializers.IntegerField()

class SpinResponseSerializer(serializers.Serializer):
    results = serializers.ListField(child=SpinResultItemSerializer())
    balance = serializers.IntegerField()
    total_win = serializers.IntegerField()
    error = serializers.CharField(required=False)

class CoinflipResponseSerializer(serializers.Serializer):
    result = serializers.IntegerField(help_text="0=loss, 1=win, 2=insufficient balance")
    balance = serializers.IntegerField()
    win = serializers.IntegerField()
    flip_result = serializers.IntegerField(allow_null=True, help_text="0 or 1")