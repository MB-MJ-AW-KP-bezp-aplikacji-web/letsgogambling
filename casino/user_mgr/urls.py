from django.urls import path
import casino.user_mgr.views as v

urlpatterns = [
    path("profile/", v.profile_page, name="profile"),
    path("add_money/", v.add_money, name="add_money"),
    path("add_money/magic_money", v.magic_money_button, name="magic_money_button"),
    # path("add_money/challenge", v.challenge, name="challenge")
]