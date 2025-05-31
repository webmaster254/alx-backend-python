from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')

app_name = 'chats'

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Views
    path('', include(router.urls)),
    
    # Custom endpoints
    path('conversations/<uuid:conversation_id>/messages/', 
         views.ConversationMessagesView.as_view(), 
         name='conversation-messages'),
    path('conversations/<uuid:conversation_id>/mark_read/', 
         views.MarkConversationAsReadView.as_view(), 
         name='mark-conversation-read'),
    path('conversations/user/<uuid:user_id>/', 
         views.UserConversationsView.as_view(), 
         name='user-conversations'),
]
