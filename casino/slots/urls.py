from django.urls import path
import casino.slots.views as v

urlpatterns = [
    path("", v.slots, name="slots"),
    # path("spin/", v.spin, name="spin")
]