"""Module with configuration of admin panel for chat app."""

from django.contrib import admin

from messenger.chat.models import Message, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin panel configuration for Room model."""

    list_display = ('id', 'name')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin panel configuration for Message model."""

    list_display = ('id', 'user', 'text', 'timestamp')
