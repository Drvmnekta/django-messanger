"""Module for Rooms views."""

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from chat.models import Message, Room, RoomType

User = get_user_model()


class RoomBaseView(LoginRequiredMixin):
    """Base view class for Room objects."""

    model = Room
    fields = ['name', 'participant']
    success_url = reverse_lazy('chat:room_list')

    def get_queryset(self):
        """Get queryset for view.

        Returns:
            queryset of rooms to view.
        """
        if self.request.user.is_superuser:
            return Room.objects.all()
        return Room.objects.filter(participant__in=[self.request.user])

    def get_object(self, queryset=None):
        """Get object for view.

        Returns:
            room object to view.

        Raises:
            PermissionDenied: if user tries to get room he isn't member of.
        """
        room_name = self.kwargs.get('room_name')
        if room_name:
            room = get_object_or_404(Room, name=room_name)
            if self.request.user in room.participant.all():
                return room
            raise PermissionDenied


class RoomListView(RoomBaseView, ListView):
    """View for list of Room objects."""

    template_name = 'rooms_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        """Get context for rendering.

        Args:
            object_list: list of objects for list view.

        Returns:
            new context dictionary.
        """
        context = super().get_context_data(**kwargs)
        context['room_list'] = Room.objects.filter(type=RoomType.common_channel)
        for room in context['room_list']:
            room.unread = Message.objects.filter(~Q(read_users__in=[self.request.user]), room=room).count()
        return context


class RoomDetailView(RoomBaseView, DetailView):
    """Detail view for Room chatbox."""

    template_name = 'room_detail.html'

    def get_context_data(self, **kwargs):
        """Get context for rendering.

        Returns:
            new context dictionary.
        """
        context = super().get_context_data(**kwargs)
        room_name = self.kwargs.get('room_name')
        room = Room.objects.get(name=room_name)
        if room_name and room.type == RoomType.direct_messages:
            context['direct_user'] = room_name.replace('direct', '').replace(self.request.user.username, '')
            context['direct_user'] = context['direct_user'].replace('_', '')
        if room_name and room.type == RoomType.common_channel:
            context['participants'] = [part.username for part in room.participant.all()]
        return context


class RoomCreateView(RoomBaseView, CreateView):
    """View for Room objects creation."""

    template_name = 'room_form.html'

    def form_valid(self, form):
        """Handle valid form.

        Args:
            form to handle - add field.

        Returns:
            handled form.
        """
        form.instance.type = RoomType.common_channel
        form.save()
        return super().form_valid(form)


class RoomUpdateView(RoomBaseView, UpdateView):
    """View for Room objects update."""

    template_name = 'room_form.html'

    def get_object(self, queryset=None):
        """Get object to view.

        Args:
            queryset: object queryset where to get object for view.

        Returns:
            object to view.

        Raises:
            PermissionDenied: if user tries to update direct messages room.
        """
        room_name = self.kwargs.get('room_name')
        if room_name and 'direct__' in room_name:
            raise PermissionDenied
        return Room.objects.get(name=room_name)


class RoomDeleteView(RoomBaseView, DeleteView):
    """View for Room objects delete."""

    template_name = 'room_confirm_delete.html'


class DirectListView(LoginRequiredMixin, ListView):
    """View for list of direct messages chats."""

    template_name = 'user_direct_list.html'
    queryset = User.objects.all()

    def get_context_data(self, *, object_list=None, **kwargs):
        """Get context for rendering.

        Args:
            object_list: list of objects for list view.

        Returns:
            new context dictionary.
        """
        context = super().get_context_data(**kwargs)
        context['room_list'] = Room.objects.filter(type=RoomType.common_channel)
        for user in context['user_list']:
            try:
                direct_room = Room.objects.get(name=f'__{self.request.user.username}_{user.username}_direct__')
            except ObjectDoesNotExist:
                try:
                    direct_room = Room.objects.get(name=f'__{user.username}_{self.request.user.username}_direct__')
                except ObjectDoesNotExist:
                    user.unread = 0
                    continue
            user.unread = Message.objects.filter(~Q(read_users__in=[self.request.user]), room=direct_room).count()
        return context


class DirectDetailView(View, LoginRequiredMixin):
    """View-class for direct messages room."""

    def get(self, request, *args, **kwargs):
        """Handle get-request.

        Args:
            request: HTTPRequest to handle.

        Returns:
            redirect for direct messages room.

        Raises:
            PermissionDenied: if user tries to create direct messages room with himself.
        """
        first_user = request.user
        second_user = get_object_or_404(User, username=self.kwargs.get('username'))
        if first_user == second_user:
            raise PermissionDenied
        try:
            room = Room.objects.get(name=f'__{first_user.username}_{second_user.username}_direct__')
        except ObjectDoesNotExist:
            try:
                room = Room.objects.get(name=f'__{second_user.username}_{first_user.username}_direct__')
            except ObjectDoesNotExist:
                room = Room.objects.create(
                    type=RoomType.direct_messages,
                    name=f'__{first_user.username}_{second_user.username}_direct__',
                )
                room.participant.add(first_user.id, second_user.id)
        return redirect('chat:room_chatbox', room_name=room.name)


class DirectDeleteView(View, LoginRequiredMixin):
    """View-class for direct messages room delete."""

    def get(self, request, *args, **kwargs):
        """Handle get-request.

        Args:
            request: HTTPRequest to handle.

        Returns:
            redirect for direct messages room delete.

        Raises:
            PermissionDenied: if user tries to delete direct messages room with himself.
        """
        first_user = request.user
        second_user = get_object_or_404(User, username=self.kwargs.get('username'))
        if first_user == second_user:
            raise PermissionDenied
        try:
            room = Room.objects.get(name=f'__{first_user.username}_{second_user.username}_direct__')
        except ObjectDoesNotExist:
            try:
                room = Room.objects.get(name=f'__{second_user.username}_{first_user.username}_direct__')
            except ObjectDoesNotExist:
                return redirect('chat:room_list')
        return redirect('chat:room_delete', room_name=room.name)
