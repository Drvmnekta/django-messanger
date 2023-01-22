"""Module with main urls of the project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include(('chat.urls', 'chat'), namespace='chat')),
    path('chat/', include(('chat.urls', 'messenger.chat'), namespace='chat')),
]
