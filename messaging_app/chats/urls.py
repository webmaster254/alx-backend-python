from django.urls import path, include
from rest_framework import routers
from . import views

app_name = 'chats'

# Create a router for chat-specific endpoints
router = routers.DefaultRouter()

# Register viewsets with the router
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    # Include DRF router URLs
    path('', include(router.urls)),
    
    # Search endpoint
    path('search/messages/', views.search_messages, name='search-messages'),
    
    # Conversation endpoints
    path('conversations/<uuid:conversation_id>/messages/', 
         views.ConversationViewSet.as_view({'get': 'messages'}), 
         name='conversation-messages'),
    path('conversations/<uuid:conversation_id>/add_participant/', 
         views.ConversationViewSet.as_view({'post': 'add_participant'}), 
         name='add-participant'),
    
    # Message endpoints
    path('messages/mark_read/', 
         views.MessageViewSet.as_view({'post': 'mark_multiple_as_read'}), 
         name='mark-messages-read'),
    path('messages/<uuid:pk>/mark_read/', 
         views.MessageViewSet.as_view({'post': 'mark_as_read'}), 
         name='mark-message-read'),
]
