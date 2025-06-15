from django.db import models
from django.db.models import Q


class UnreadMessagesManager(models.Manager):
    """
    Custom manager to handle unread messages with optimized queries.
    Provides methods to filter unread messages for specific users with performance optimizations.
    """
    
    def unread_for_user(self, user):
        """
        Get all unread messages for a specific user (where they are the receiver).
        Uses select_related to optimize related lookups.
        """
        return self.get_queryset().filter(
            receiver=user,
            is_read=False
        ).select_related('sender').order_by('-sent_at')
    
    def count_for_user(self, user):
        """
        Get the count of unread messages for a user efficiently.
        """
        return self.get_queryset().filter(
            receiver=user,
            is_read=False
        ).count()
    
    def threaded_for_user(self, user):
        """
        Get unread messages for a user with thread information optimized.
        Includes parent message data for threading context.
        """
        return self.get_queryset().filter(
            receiver=user,
            is_read=False
        ).select_related(
            'sender',
            'parent_message__sender'
        ).prefetch_related(
            'replies'  # Prefetch replies for thread context
        ).only(
            'id', 'content', 'sent_at', 'sender__id', 'sender__email',
            'sender__first_name', 'sender__last_name', 'parent_message_id',
            'parent_message__content', 'parent_message__sender__email'
        ).order_by('-sent_at')
    
    def conversation_unread(self, user, conversation_partner):
        """
        Get unread messages in a specific conversation between two users.
        Optimized for conversation view.
        """
        return self.get_queryset().filter(
            Q(sender=conversation_partner, receiver=user, is_read=False)
        ).select_related(
            'sender'
        ).only(
            'id', 'content', 'sent_at', 'sender__id', 'sender__email',
            'parent_message_id'
        ).order_by('sent_at')  # Chronological order for conversations
    
    def bulk_mark_read(self, user, message_ids=None):
        """
        Efficiently mark multiple messages as read for a user.
        If message_ids provided, mark only those messages, otherwise mark all unread.
        """
        queryset = self.get_queryset().filter(
            receiver=user,
            is_read=False
        )
        
        if message_ids:
            queryset = queryset.filter(id__in=message_ids)
        
        return queryset.update(
            is_read=True,
            read_at=models.functions.Now()
        )
    
    def recent_unread(self, user, hours=24):
        """
        Get recent unread messages within specified hours.
        Default to last 24 hours.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        return self.get_queryset().filter(
            receiver=user,
            is_read=False,
            sent_at__gte=cutoff_time
        ).select_related(
            'sender'
        ).only(
            'id', 'content', 'sent_at', 'sender__email'
        ).order_by('-sent_at')
    
    def priority_unread(self, user):
        """
        Get unread messages with priority indicators.
        Useful for inbox prioritization.
        """
        return self.get_queryset().filter(
            receiver=user,
            is_read=False
        ).select_related(
            'sender'
        ).only(
            'id', 'content', 'sent_at', 'sender__email',
            'parent_message_id'
        ).extra(
            select={
                'is_reply': 'CASE WHEN parent_message_id IS NOT NULL THEN 1 ELSE 0 END',
                'hours_old': "EXTRACT(EPOCH FROM (NOW() - sent_at)) / 3600"
            }
        ).order_by('-sent_at')


class ThreadedMessagesManager(models.Manager):
    """
    Manager for handling threaded message operations efficiently.
    Complements UnreadMessagesManager for complete message management.
    """
    
    def root_messages_for_user(self, user):
        """
        Get top-level messages (not replies) for a user with optimized queries.
        """
        return self.get_queryset().filter(
            Q(sender=user) | Q(receiver=user),
            parent_message__isnull=True
        ).select_related(
            'sender', 'receiver'
        ).prefetch_related(
            'replies__sender',
            'replies__receiver'
        ).only(
            'id', 'content', 'sent_at', 'is_read',
            'sender__id', 'sender__email',
            'receiver__id', 'receiver__email'
        ).order_by('-sent_at')
    
    def thread_with_replies(self, message_id):
        """
        Get a specific message thread with all replies optimized.
        """
        return self.get_queryset().filter(
            Q(id=message_id) | Q(parent_message_id=message_id)
        ).select_related(
            'sender', 'receiver', 'parent_message'
        ).only(
            'id', 'content', 'sent_at', 'is_read',
            'sender__email', 'receiver__email',
            'parent_message_id'
        ).order_by('sent_at')
