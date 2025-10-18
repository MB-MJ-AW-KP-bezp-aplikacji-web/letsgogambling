from django.urls import path
import casino.user_mgr.views as v

urlpatterns = [
    path("", v.profile_page, name="profile"),
    path("magic-money/", v.magic_money_button, name="magic_money_button"),
]