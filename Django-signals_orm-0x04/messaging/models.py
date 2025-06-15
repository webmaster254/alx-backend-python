from django.db import models

# Create your models here.
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
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
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
        db_table = 'notifications'
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
