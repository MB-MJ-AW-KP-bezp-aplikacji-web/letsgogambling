from django.urls import re_path
import casino.roulette.views as v

urlpatterns = [
    re_path(r"^$", v.roulette, name="roulette")
]