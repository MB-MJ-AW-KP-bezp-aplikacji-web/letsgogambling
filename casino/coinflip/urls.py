from django.urls import path
import casino.coinflip.views as v

urlpatterns = [
    path("", v.coinflip, name="coinflip")
]
