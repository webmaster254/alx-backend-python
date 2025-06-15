import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings

from django.contrib.auth.models import User
from .managers import UnreadMessagesManager, ThreadedMessagesManager


class Message(models.Model):
    """Model representing a message in a conversation"""
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messaging_sent_messages',
        help_text='The user who sent this message'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messaging_received_messages',
        help_text='The user who received this message'
    )
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True,
        help_text='The message this is a reply to (for threaded conversations)'
    )
    content = models.TextField(
        help_text='The actual message content'
    )
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the message has been read by the recipient(s)'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the message was read by the recipient'
    )
    edited = models.BooleanField(
        default=False,
        help_text='Whether this message has been edited'
    )
    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the message was last edited'
    )
    
    sent_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Custom managers
    objects = models.Manager()  # Default manager
    unread = UnreadMessagesManager()  # Custom manager for unread messages
    threaded = ThreadedMessagesManager()  # Custom manager for threaded operations

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        db_table = 'messaging_messages'

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    def mark_as_edited(self):
        """Mark this message as edited"""
        if not self.edited:
            self.edited = True
            self.edited_at = timezone.now()
            self.save()
            
    def __str__(self):
        return f"{self.sender.email} to {self.receiver.email}: {self.content[:50]}"

class MessageHistory(models.Model):
    """Model to store the history of message edits"""
    history_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='History ID'
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='edit_history',
        help_text='The message this history entry belongs to'
    )
    old_content = models.TextField(
        help_text='The previous content of the message before the edit'
    )
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messaging_message_edits',
        help_text='The user who made this edit'
    )
    edit_timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When this edit was made'
    )
    edit_reason = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Optional reason for the edit'
    )

    class Meta:
        db_table = 'messaging_message_history'
        verbose_name = 'Message History'
        verbose_name_plural = 'Message Histories'
        ordering = ['-edit_timestamp']

    def __str__(self):
        return f"Edit history for message {self.message.message_id} by {self.edited_by.email}"



class Notification(models.Model):
    """Model representing notifications for users"""
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('system', 'System Notification'),
        ('reminder', 'Reminder'),
    ]

    notification_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='Notification ID'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messaging_notifications',
        help_text='The user who will receive this notification'
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text='The message that triggered this notification (if applicable)'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='message',
        help_text='Type of notification'
    )
    title = models.CharField(
        max_length=100,
        help_text='Notification title'
    )
    content = models.TextField(
        help_text='Notification content/description'
    )
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the notification has been read'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the notification was created'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the notification was read'
    )

    class Meta:
        db_table = 'messaging_notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"

    def mark_as_read(self):
        """Mark this notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
