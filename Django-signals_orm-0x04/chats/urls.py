from django.urls import path, include
from rest_framework import routers
from rest_framework_nested.routers import NestedDefaultRouter
from . import views

app_name = 'chats'

# Create a router for chat-specific endpoints
router = routers.DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'users', views.UserViewSet, basename='user')

# Nested router for messages under conversations
conversation_router = NestedDefaultRouter(
    router, r'conversations', lookup='conversation')
conversation_router.register(r'messages', views.MessageViewSet, basename='conversation-messages')

# Register messages at the root level as well
router.register(r'messages', views.MessageViewSet, basename='message')

urlpatterns = [
    # Include DRF router URLs
    path('', include(router.urls)),
    path('', include(conversation_router.urls)),
    
    # Search endpoint
    path('search/messages/', views.search_messages, name='search-messages'),
    
    # Conversation endpoints
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
    
    # User account management
    path('delete-account/', views.delete_user, name='delete_user'),
]
