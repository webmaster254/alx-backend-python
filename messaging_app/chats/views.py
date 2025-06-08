from datetime import datetime
import logging

from rest_framework import viewsets, status, permissions, filters, serializers
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsParticipantOfConversation
from .filters import MessageFilter, ConversationFilter
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, UserSerializer

# Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()

# Import custom pagination classes
from .pagination import StandardResultsSetPagination, MessageLimitOffsetPagination, MessageCursorPagination

class ConversationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows conversations to be viewed or edited.
    """
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsParticipantOfConversation]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ConversationFilter
    search_fields = ['group_name', 'participants__email', 'participants__first_name', 'participants__last_name']
    ordering_fields = ['updated_at', 'created_at']
    ordering = ['-updated_at']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        This view should return a list of all conversations
        for the currently authenticated user.
        """
        queryset = self.queryset.filter(participants=self.request.user)
        
        # Filter by conversation type (group or direct)
        is_group = self.request.query_params.get('is_group', None)
        if is_group is not None:
            queryset = queryset.filter(is_group=is_group.lower() == 'true')
        
        # Search by participant email
        participant_email = self.request.query_params.get('participant_email', None)
        if participant_email:
            queryset = queryset.filter(
                participants__email__iexact=participant_email
            )
        
        return queryset.distinct()

    def perform_create(self, serializer):
        """Create a new conversation with the current user as a participant."""
        participants = serializer.validated_data.get('participants', [])
        is_group = serializer.validated_data.get('is_group', False)
        
        if not is_group and len(participants) != 1:
            raise serializers.ValidationError({
                'participants': 'Direct messages must have exactly one participant.'
            })
        
        conversation = serializer.save()
        conversation.participants.add(self.request.user)
        
        # For direct messages, ensure the other participant is added
        if not is_group and participants:
            conversation.participants.add(participants[0])
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add a participant to a conversation."""
        conversation = self.get_object()
        
        # Check if the current user is a participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.get(pk=user_id)
            
            # Check if user is already a participant
            if conversation.participants.filter(id=user_id).exists():
                return Response(
                    {'status': 'User is already a participant'},
                    status=status.HTTP_200_OK
                )
                
            conversation.participants.add(user)
            serializer = self.get_serializer(conversation)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages for a conversation."""
        conversation = self.get_object()
        messages = conversation.messages.all().order_by('-sent_at')
        
        # Pagination
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
            
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows messages to be viewed or edited.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsParticipantOfConversation]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MessageFilter
    search_fields = ['message_body', 'sender__email', 'sender__first_name', 'sender__last_name']
    ordering_fields = ['sent_at', 'updated_at']
    ordering = ['-sent_at']
    pagination_class = MessageCursorPagination  # Using cursor pagination for messages

    def get_queryset(self):
        """
        This view should return a list of all messages from conversations
        where the current user is a participant.
        """
        queryset = self.queryset.filter(conversation__participants=self.request.user)
        
        # Filter by conversation
        conversation_id = self.request.query_params.get('conversation', None)
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Filter by sender
        sender_id = self.request.query_params.get('sender', None)
        if sender_id:
            queryset = queryset.filter(sender_id=sender_id)
            
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if date_from:
            queryset = queryset.filter(sent_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(sent_at__date__lte=date_to)
            
        return queryset.distinct()

    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
        
    def perform_create(self, serializer):
        """Create a new message with the current user as the sender."""
        conversation = serializer.validated_data['conversation']
        
        # Check if the user is a participant in the conversation
        if not conversation.participants.filter(id=self.request.user.id).exists():
            raise serializers.ValidationError({
                'conversation': 'You are not a participant in this conversation.'
            })
            
        serializer.save(sender=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a message as read."""
        message = self.get_object()
        
        # Only mark as read if the message is not from the current user
        if message.sender != request.user:
            message.mark_as_read()
            return Response(
                {'status': 'message marked as read'},
                status=status.HTTP_200_OK
            )
        return Response(
            {'status': 'message not marked as read (own message)'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def mark_multiple_as_read(self, request):
        """Mark multiple messages as read."""
        message_ids = request.data.get('message_ids', [])
        if not message_ids:
            return Response(
                {'error': 'message_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Only update messages that belong to conversations the user is in
        updated_count = Message.objects.filter(
            id__in=message_ids,
            conversation__participants=request.user
        ).exclude(
            sender=request.user  # Don't mark own messages as read
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'status': f'{updated_count} messages marked as read'
        })
    
    def perform_create(self, serializer):
        """Create a new message with the current user as the sender."""
        conversation = serializer.validated_data['conversation']
        
        # Check if user is a participant in the conversation
        if not conversation.participants.filter(id=self.request.user.id).exists():
            raise PermissionDenied("You are not a participant in this conversation.")
        
        message = serializer.save(sender=self.request.user)
        
        # Update conversation's updated_at timestamp
        conversation.save()
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a message and mark it as read if it's not from the current user."""
        message = self.get_object()
        
        # Mark as read if the message is not from the current user
        if message.sender != request.user and not message.is_read:
            message.mark_as_read()
            
        serializer = self.get_serializer(message)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a specific message as read."""
        message = self.get_object()
        
        # Only mark as read if the message is not from the current user
        if message.sender != request.user and not message.is_read:
            message.mark_as_read()
            return Response({'status': 'Message marked as read'})
        
        return Response(
            {'status': 'Message was already read or sent by you'},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['first_name', 'last_name', 'date_joined']
    ordering = ['first_name', 'last_name']
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        This view should return a list of all users
        except the currently authenticated user.
        """
        queryset = User.objects.exclude(id=self.request.user.id)
        
        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
            
        return queryset.distinct()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_messages(request):
    """
    Search messages across all conversations the user is a part of.
    """
    query = request.query_params.get('q', None)
    if not query:
        return Response(
            {'error': 'Search query parameter "q" is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Search in messages where the user is a participant
    messages = Message.objects.filter(
        Q(conversation__participants=request.user) &
        (
            Q(message_body__icontains=query) |
            Q(sender__first_name__icontains=query) |
            Q(sender__last_name__icontains=query) |
            Q(sender__email__icontains=query)
        )
    ).order_by('-sent_at')
    
    # Paginate results
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(messages, request)
    
    if page is not None:
        serializer = MessageSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = MessageSerializer(messages, many=True, context={'request': request})
    return Response(serializer.data)
