from django.urls import path
import casino.login.views as v

urlpatterns = [
    path("", v.login_page, name="login_page"),
    path("l/", v.login_user, name="login"),
    path("r/", v.register_user, name="register"),
    path("lll/", v.logout_user, name="logout")
]
