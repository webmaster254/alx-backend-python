"""
Django signals for automatic notification creation when messages are sent.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, Notification


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Signal handler that automatically creates a notification 
    when a new message is created.
    
    This signal listens for new Message instances and creates
    notifications for all participants in the conversation
    except the sender.
    """
    if created:  # Only trigger for new messages, not updates
        # Get all participants in the conversation except the sender
        participants = instance.conversation.participants.exclude(
            user_id=instance.sender.user_id
        )
        
        # Create notifications for each participant (receiver)
        for participant in participants:
            Notification.objects.create(
                user=participant,
                message=instance,
                notification_type='message',
                title=f'New message from {instance.sender.first_name or instance.sender.email}',
                content=f'You have received a new message: "{instance.message_body[:50]}{"..." if len(instance.message_body) > 50 else ""}"'
            )


@receiver(post_save, sender=Message)
def log_message_creation(sender, instance, created, **kwargs):
    """
    Optional signal handler for logging message creation.
    This can be useful for debugging and monitoring.
    """
    if created:
        participants = instance.conversation.participants.exclude(
            user_id=instance.sender.user_id
        )
        participant_count = participants.count()
        
        print(f"📧 New message created:")
        print(f"   From: {instance.sender.email}")
        print(f"   Conversation: {instance.conversation}")
        print(f"   Content: {instance.message_body[:100]}{'...' if len(instance.message_body) > 100 else ''}")
        print(f"   📱 {participant_count} notification(s) created for participant(s)")


@receiver(post_save, sender=Notification)
def log_notification_creation(sender, instance, created, **kwargs):
    """
    Optional signal handler for logging notification creation.
    """
    if created:
        print(f"🔔 Notification created for {instance.user.email}: {instance.title}")
