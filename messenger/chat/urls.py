"""Module with chat urls."""

from django.urls import path

from messenger.chat import views

urlpatterns = [
    path('', views.RoomListView.as_view(), name='room_list'),
    path('create/', views.RoomCreateView.as_view(), name='room_create'),
    path('direct/', views.DirectListView.as_view(), name='direct_list'),
    path('<str:room_name>/', views.RoomDetailView.as_view(), name='room_chatbox'),
    path('<str:room_name>/update/', views.RoomUpdateView.as_view(), name='room_update'),
    path('<str:room_name>/delete/', views.RoomDeleteView.as_view(), name='room_delete'),
    path('direct/<str:username>/', views.DirectDetailView.as_view(), name='direct_chatbox'),
    path('direct/<str:username>/delete/', views.DirectDeleteView.as_view(), name='direct_delete'),
]
