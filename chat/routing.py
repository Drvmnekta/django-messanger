"""Module with routing."""

from channels.routing import URLRouter
from django.urls import re_path

from paumr.chat import consumers

url_router = URLRouter([
    re_path(r'^ws/chat/(?P<room_name>.+)/$', consumers.ChatConsumer.as_asgi()),
])
