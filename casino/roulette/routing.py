"""
WebSocket URL routing for roulette game.
Maps ws:// connections to the appropriate consumer.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/roulette/$', consumers.RouletteConsumer.as_asgi()),
]
