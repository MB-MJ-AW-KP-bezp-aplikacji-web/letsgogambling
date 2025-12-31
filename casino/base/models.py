from django.db import models
from casino.login.models import User


# Create your models here.
class Codes(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField()
    value = models.IntegerField()

class UsedCodes(models.Model):
    id = models.IntegerField(primary_key=True)
    u_id = models.ForeignKey(Codes, on_delete=models.CASCADE)
    c_id = models.ForeignKey(User, on_delete=models.CASCADE)

class History(models.Model):
    id = models.IntegerField(primary_key=True)
    u_id = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    cashout_time = models.DateTimeField()
