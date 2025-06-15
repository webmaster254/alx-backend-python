"""
URL configuration for messaging_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from chats.auth import CustomTokenObtainPairView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Import views after apps are loaded to avoid circular imports
from django.apps import apps

# Schema view for API documentation
schema_view = get_schema_view(
   openapi.Info(
      title="Messaging API",
      default_version='v1',
      description="API for the Messaging Application",
      terms_of_service="https://www.jmacharia.co.ke/",
      contact=openapi.Contact(email="josephm2800@gmail.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# Create a router and register our viewsets
router = DefaultRouter()

# Only register views if the app is loaded to avoid AppRegistryNotReady
if apps.is_installed('chats'):
    from chats.views import ConversationViewSet, MessageViewSet, UserViewSet
    
    # Register viewsets with the router
    router.register(r'conversations', ConversationViewSet, basename='conversation')
    router.register(r'messages', MessageViewSet, basename='message')
    router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # API endpoints - v1
    path('api/v1/', include([
        # Include router URLs
        path('', include(router.urls)),
        
        # Authentication
        path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        
        # DRF browsable API auth
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    ])),
    
    # Messaging app URLs
    path('messaging/', include('messaging.urls')),
    
    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', 
            schema_view.without_ui(cache_timeout=0), 
            name='schema-json'),
    re_path(r'^swagger/$', 
            schema_view.with_ui('swagger', cache_timeout=0), 
            name='schema-swagger-ui'),
    re_path(r'^redoc/$', 
            schema_view.with_ui('redoc', cache_timeout=0), 
            name='schema-redoc'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
