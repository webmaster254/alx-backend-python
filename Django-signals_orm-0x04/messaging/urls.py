from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Account management
    path('delete-account/', views.delete_user, name='delete_user'),
    path('delete-account-page/', views.delete_account_page, name='delete_account_page'),
    
    # Threaded conversation endpoints
    path('messages/threaded/', views.get_threaded_messages, name='get_threaded_messages'),
    path('messages/thread/<uuid:message_id>/', views.get_message_thread, name='get_message_thread'),
    path('messages/reply/', views.create_reply, name='create_reply'),
    
    # Unread messages endpoints
    path('messages/unread/', views.unread_messages, name='unread_messages'),
    path('messages/<uuid:message_id>/mark-read/', views.mark_as_read, name='mark_as_read'),
    
    # UI endpoints
    path('ui/threaded/', views.threaded_messages_ui, name='threaded_messages_ui'),
]
