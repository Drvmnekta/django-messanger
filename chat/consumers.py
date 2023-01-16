"""Module with websocket consumers for chat app."""

import json
from datetime import datetime
from itertools import chain
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db.models import Q

from chat.models import Message, Room

MESSAGES_PAGINATE = 20


class ChatConsumer(WebsocketConsumer):
    """Consumer for chatbox."""

    def __init__(self, *args, **kwargs):
        """Create ChatConsumer object."""
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None
        self.unread_count = 0
        self.start_msgs = None
        self.down_zero_msg_id = 0
        self.up_zero_msg_id = 0

    def get_start_messages(self, room_name):
        """Get messages for start with chatbox.

        Args:
            room_name: name of the chatroom.

        Returns:
            List with messages data to render.
        """
        room_messages = Message.objects.filter(room__name=room_name)
        all_unread_msgs = room_messages.filter(~Q(read_users__id=self.scope['user'].id)).order_by('id')
        unread_to_paginate = 0
        for msg in all_unread_msgs:
            msg.read = False
        if len(all_unread_msgs) >= MESSAGES_PAGINATE:
            start_msgs = all_unread_msgs[:MESSAGES_PAGINATE]
            unread_to_paginate = len(all_unread_msgs) - MESSAGES_PAGINATE
        elif all_unread_msgs and MESSAGES_PAGINATE > len(all_unread_msgs):
            need_msgs_amount = MESSAGES_PAGINATE - len(all_unread_msgs)
            old_msgs = room_messages.filter(Q(read_users__id=self.scope['user'].id)).order_by('-id')[:need_msgs_amount]
            for msg in old_msgs:
                msg.read = msg.read_users.count() != 1
            start_msgs = sorted(
                chain(old_msgs, all_unread_msgs),
                key=lambda instance: instance.id,
            )
        else:
            old_msgs = Message.objects.filter(room__name=room_name)[:MESSAGES_PAGINATE:-1]
            if old_msgs:
                start_msgs = old_msgs
                for msg in start_msgs:
                    msg.read = msg.read_users.count() != 1
            else:
                self.up_zero_msg_id = 0
                self.down_zero_msg_id = 0
                return None, unread_to_paginate
        for message in start_msgs:
            message.time = datetime.strftime(message.timestamp, '%H:%M')
            message.date = datetime.strftime(message.timestamp, '%d.%b.%Y')
        self.up_zero_msg_id = start_msgs[0].id
        self.down_zero_msg_id = start_msgs[-1].id
        return start_msgs, unread_to_paginate

    def get_paginate_down(self, page):
        """Get next messages.

        Args:
            page: page to paginate.

        Returns:
            List with message data to render.
        """
        all_unread_msgs = Message.objects.filter(~Q(read_users__id=self.scope['user'].id), room=self.room).count()
        if all_unread_msgs - MESSAGES_PAGINATE < 0:
            all_unread_msgs = 0
        else:
            all_unread_msgs -= MESSAGES_PAGINATE
        start_paginate = self.down_zero_msg_id + 1 + (MESSAGES_PAGINATE * (page - 1))
        end_paginate = self.down_zero_msg_id + (MESSAGES_PAGINATE * page)
        messages = Message.objects.filter(Q(id__gte=start_paginate, id__lte=end_paginate), room=self.room)[::-1]
        for msg in messages:
            msg.read = Message.objects.filter(pk=msg.id, read_users__id=self.scope['user'].id).exists()
        return messages, all_unread_msgs

    def get_paginate_up(self, page):
        """Get previous messages.

        Args:
            page: page to paginate.

        Returns:
            List with message data to render.
        """
        start_paginate = self.up_zero_msg_id - 1 - (MESSAGES_PAGINATE * (page - 1))
        end_paginate = self.up_zero_msg_id - (MESSAGES_PAGINATE * page)
        if end_paginate <= 0:
            end_paginate = 1
        messages = Message.objects.filter(Q(id__lte=start_paginate, id__gte=end_paginate), room=self.room)
        for msg in messages:
            msg.read = Message.objects.filter(pk=msg.id, read_users__id=self.scope['user'].id).exists()
        return messages

    def send_online_user_list(self):
        """Send list of users online."""
        online_user_list = settings.REDIS_CLIENT.smembers(f'{self.room_name}_onlines')
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {
                'type': 'online_users',
                'users': [username.decode('utf-8') for username in online_user_list],
            },
        )

    def connect(self):
        """Consume socket connect."""
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.room = Room.objects.get(name=self.room_name)
        self.user = self.scope['user']
        self.accept()

        messages, unread_count = self.get_start_messages(self.room_name)
        self.start_msgs = [
            {
                'message_id': msg.id,
                'message': msg.text,
                'user': msg.user.username,
                'time': msg.time,
                'date': msg.date,
                'read_message': msg.read,
            }
            for msg in messages
        ] if messages else None
        self.unread_count = unread_count

        async_to_sync(self.channel_layer.send)(
            self.channel_name,
            {
                'type': 'chat_message',
                'messages': self.start_msgs,
                'count': self.unread_count,
            },
        )

        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {'type': 'user_join', 'user': self.user.username},
        )
        settings.REDIS_CLIENT.sadd(f'{self.room_name}_onlines', bytes(self.user.username, 'utf-8'))
        self.send_online_user_list()

    def disconnect(self, close_code):
        """Consume socket disconnect.

        Args:
            close_code: code socket closed with.
        """
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {'type': 'user_leave', 'user': self.user.username},
        )

        settings.REDIS_CLIENT.srem(f'{self.room_name}_onlines', bytes(self.user.username, 'utf-8'))
        self.send_online_user_list()

    def receive(self, text_data=None, bytes_data=None):
        """Consume socket receiving.

        Args:
            text_data: text data from frontend contains message;
            bytes_data: bytes data from frontend.
        """
        text_data_json = json.loads(text_data)

        if not self.user.is_authenticated:
            return

        if text_data_json['type'] == 'chat_message':
            message = text_data_json['message']
            new_message = Message.objects.create(user=self.user, room=self.room, text=message)
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'messages': [{
                        'user': self.user.username,
                        'message': message,
                        'message_id': new_message.id,
                        'time': datetime.strftime(new_message.timestamp, '%H:%M'),
                        'date': datetime.strftime(new_message.timestamp, '%d.%b.%Y'),
                        'read_message': False,
                    }],
                },
            )

        if text_data_json['type'] == 'user_typing':
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user': self.user.username,
                    'message': f'{self.user.username} печатает...',
                },
            )

        if text_data_json['type'] == 'user_stop_typing':
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_stop_typing',
                    'message': None,
                },
            )

        if text_data_json['type'] == 'paginate_up':
            messages = self.get_paginate_up(page=text_data_json['page'])
            messages = [
                {
                    'message_id': msg.id,
                    'message': msg.text,
                    'user': msg.user.username,
                    'time': datetime.strftime(msg.timestamp, '%H:%M'),
                    'date': datetime.strftime(msg.timestamp, '%d.%b.%Y'),
                    'read_message': msg.read,
                }
                for msg in messages
            ]

            async_to_sync(self.channel_layer.send)(
                self.channel_name,
                {
                    'type': 'paginate_up',
                    'messages': messages,
                },
            )

        if text_data_json['type'] == 'paginate_down':
            messages, count = self.get_paginate_down(page=text_data_json['page'])
            messages = [
                {
                    'message_id': msg.id,
                    'message': msg.text,
                    'user': msg.user.username,
                    'time': datetime.strftime(msg.timestamp, '%H:%M'),
                    'date': datetime.strftime(msg.timestamp, '%d.%b.%Y'),
                    'read_message': msg.read,
                }
                for msg in messages
            ]

            async_to_sync(self.channel_layer.send)(
                self.channel_name,
                {
                    'type': 'paginate_down',
                    'messages': messages,
                    'count': count,
                },
            )

        if text_data_json['type'] == 'read_message':
            message = Message.objects.get(pk=text_data_json['id'])
            message.read_users.add(self.scope['user'])
            if message.read_users.count() == 2:
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'read_message',
                        'message_id': text_data_json['id'],
                    },
                )

    def chat_message(self, event):
        """Send message to chatbox.

        Args:
            event: message to send.
        """
        self.send(text_data=json.dumps(event))

    def user_join(self, event):
        """Send message to chatbox.

        Args:
            event: message about user joining to send.
        """
        self.send(text_data=json.dumps(event))

    def user_leave(self, event):
        """Send message to chatbox.

        Args:
            event: message about user leaving to send.
        """
        self.send(text_data=json.dumps(event))

    def online_users(self, event):
        """Get online users list.

        Args:
            event: message with online users list.
        """
        self.send(text_data=json.dumps(event))

    def user_typing(self, event):
        """Send message to chatbox.

        Args:
            event: message about user typing.
        """
        self.send(text_data=json.dumps(event))

    def user_stop_typing(self, event):
        """Send message to chatbox.

        Args:
            event: message about user typing remove.
        """
        self.send(text_data=json.dumps(event))

    def last_read_msg(self, event):
        """Send data about read messages.

        Args:
            event: message read.
        """
        self.send(text_data=json.dumps(event))

    def paginate_up(self, event):
        """Send previous messages.

        Args:
            event: previous messages.
        """
        self.send(text_data=json.dumps(event))

    def paginate_down(self, event):
        """Send next messages.

        Args:
            event: next messages.
        """
        self.send(text_data=json.dumps(event))

    def start_messages(self, event):
        """Send message for first rendering.

        Args:
            event: start messages.
        """
        self.send(text_data=json.dumps(event))

    def read_message(self, event):
        """Send flag that message is read.

        Args:
            event: read message.
        """
        self.send(text_data=json.dumps(event))
