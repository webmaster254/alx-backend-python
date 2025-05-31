from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return conversations where the current user is a participant.
        Can be filtered by 'is_group' and 'search' query parameters.
        """
        queryset = Conversation.objects.filter(participants=self.request.user)
        
        # Filter by conversation type (group or direct)
        is_group = self.request.query_params.get('is_group')
        if is_group is not None:
            queryset = queryset.filter(is_group=is_group.lower() == 'true')
            
        # Search in group names or participant names for direct messages
        search = self.request.query_params.get('search')
        if search:
            # For group conversations, search in group_name and group_description
            group_q = Q(group_name__icontains=search) | Q(group_description__icontains=search)
            
            # For direct messages, search in other participants' names/emails
            direct_q = Q(participants__first_name__icontains=search) | \
                      Q(participants__last_name__icontains=search) | \
                      Q(participants__email__icontains=search)
            
            queryset = queryset.filter(
                (Q(is_group=True) & group_q) | 
                (Q(is_group=False) & direct_q)
            ).distinct()
            
        return queryset.order_by('-updated_at')
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        """Create a new conversation with the current user as a participant."""
        conversation = serializer.save()
        conversation.participants.add(self.request.user)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Custom action to get messages for a specific conversation.
        Supports pagination and filtering by 'unread'.
        """
        conversation = self.get_object()
        
        # Check if user is a participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {"detail": "Not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        messages = conversation.messages.all().order_by('-timestamp')
        
        # Filter by unread messages if requested
        unread_only = request.query_params.get('unread', '').lower() == 'true'
        if unread_only:
            messages = messages.filter(is_read=False).exclude(sender=request.user)
        
        # Paginate the messages
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark all unread messages in the conversation as read."""
        conversation = self.get_object()
        
        # Mark all unread messages as read
        updated = conversation.messages.filter(
            is_read=False
        ).exclude(
            sender=request.user
        ).update(
            is_read=True
        )
        
        return Response({
            'status': f'Marked {updated} messages as read',
            'conversation_id': conversation.id
        })


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages within conversations.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return messages that the current user has permission to see.
        Can be filtered by 'conversation' and 'unread'.
        """
        queryset = Message.objects.filter(
            conversation__participants=self.request.user
        )
        
        # Filter by conversation if specified
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        
        # Filter by unread messages if requested
        unread_only = self.request.query_params.get('unread', '').lower() == 'true'
        if unread_only:
            queryset = queryset.filter(
                is_read=False
            ).exclude(
                sender=self.request.user
            )
            
        return queryset.order_by('-timestamp')
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
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
