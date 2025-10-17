from django.db import models

# Create your models here.
class Codes(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField()
    value = models.FloatField()

class User(models.Model):
    id = models.IntegerField(primary_key=True)
    username = models.CharField()
    password = models.CharField()
    email = models.CharField()
    balance = models.FloatField()
    is_active = models.BooleanField()
    is_admin = models.BooleanField()

class UsedCodes(models.Model):
    id = models.IntegerField(primary_key=True)
    u_id = models.ForeignKey(Codes, on_delete=models.CASCADE)
    c_id = models.ForeignKey(User, on_delete=models.CASCADE)

class History(models.Model):
    id = models.IntegerField(primary_key=True)
    u_id = models.ForeignKey(Codes, on_delete=models.CASCADE)
    amount = models.FloatField()
    cashout_time = models.DateTimeField()
