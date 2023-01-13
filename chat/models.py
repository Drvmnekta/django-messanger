"""Module with models for chat."""

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

ROOM_NAME_MAX_LENGTH = 128


class MessageManager(models.Manager):
    """Manager for Message model."""

    def create(self, **obj_data):
        """Modify base create method.

        Args:
            obj_data: data about object to create.

        Returns:
            created object.
        """
        message = super().create(**obj_data)
        message.read_users.set([message.user])
        return message


def validate_room_name(value_to_validate):
    """Validate room name doesn't conflict with urlpatterns.

    Args:
        value_to_validate: room name to validate.

    Returns:
        validated room name.

    Raises:
        ValueError: if room name conflicts with urlpatterns.
    """
    if value_to_validate in {'direct', 'create'}:
        raise ValueError('You cannot create room named "create" or "direct".')
    return value_to_validate


class RoomType(models.TextChoices):
    """Class with choices of room type."""

    direct_messages = 1, 'Direct Messages'
    common_channel = 2, 'Common Channel'


class Room(models.Model):
    """Model of room objects."""

    name = models.CharField(max_length=ROOM_NAME_MAX_LENGTH, unique=True, validators=[validate_room_name])
    participant = models.ManyToManyField(User, blank=False)
    type = models.CharField(max_length=2, choices=RoomType.choices)

    @property
    def members_count(self):
        """Get number of participants of the room.

        Returns:
            Number of participants of the room.
        """
        return self.participant.count()

    def __str__(self):
        """Return string representation of the Room model.

        Returns:
            Room name and number of users online.
        """
        if self.type == RoomType.direct_messages:
            participants = [part.username for part in self.participant]
            return f'Direct: {" ".join.participants}'
        return f'{self.name} ({self.members_count})'


class Message(models.Model):
    """Models of message objects."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_creator')
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    text = models.CharField(blank=False, null=False, max_length=1024)
    read_users = models.ManyToManyField(User, related_name='messages_read_users')
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = MessageManager()

    class Meta:
        """Metaclass for Message model."""

        ordering = ['-timestamp']

    def __str__(self):
        """Return string representation of the Message model.

        Returns:
            Author of the message, its content and date created.
        """
        return f'{self.user.username}: {self.text} [{self.timestamp}]'
