from django.urls import path
import casino.roulette.views as v

urlpatterns = [
    path("", v.roulette, name="roulette")
]