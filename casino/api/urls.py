from django.urls import path
import casino.api.views as v

urlpatterns = [
    path("", v.ListCreate.as_view(), name="view_create_view"),
    path("spin/", v.spin_api, name="spin_api"),
    path("coinflip/", v.coinflip_api, name="coinflip_api"),
    path("balance/", v.get_balance, name="my_balance")
    # path("l/", v.login_user, name="login")
]
