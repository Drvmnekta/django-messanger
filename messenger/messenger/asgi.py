import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from messenger.chat.routing import url_router

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messenger.messenger.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(url_router),
    ),
})
