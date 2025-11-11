from rest_framework import serializers
from casino.base.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "balance"]

class SpinResultSerializer(serializers.Serializer):
    result = serializers.IntegerField()
    machine = serializers.ListField(child=serializers.ListField(child=serializers.CharField()))
    balance = serializers.IntegerField()
    win = serializers.IntegerField()