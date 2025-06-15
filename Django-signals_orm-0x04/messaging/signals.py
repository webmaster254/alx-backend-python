"""
Django signals for automatic notification creation when messages are sent.
"""
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Message, Notification, MessageHistory


@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """
    Signal handler that performs comprehensive cleanup when a user is deleted.
    
    This signal ensures all related data is properly cleaned up when a user
    account is deleted, maintaining data integrity and preventing orphaned records.
    """
    deleted_user_info = {
        'id': instance.id,
        'username': getattr(instance, 'username', 'Unknown'),
        'email': getattr(instance, 'email', 'Unknown')
    }
    
    print(f"🗑️  User deletion cleanup initiated for: {deleted_user_info}")
    
    # Count related data before cleanup for logging
    sent_messages = Message.objects.filter(sender=instance)
    received_messages = Message.objects.filter(receiver=instance)
    user_notifications = Notification.objects.filter(user=instance)
    edit_histories = MessageHistory.objects.filter(edited_by=instance)
    
    counts = {
        'sent_messages': sent_messages.count(),
        'received_messages': received_messages.count(),
        'notifications': user_notifications.count(),
        'edit_histories': edit_histories.count()
    }
    
    # Manual cleanup for any data that might not be handled by CASCADE
    # Note: Django's CASCADE should handle most of this, but we're being explicit
    
    # Clean up messages sent by the user
    if counts['sent_messages'] > 0:
        sent_messages.delete()
        print(f"   📧 Deleted {counts['sent_messages']} sent messages")
    
    # Clean up messages received by the user
    if counts['received_messages'] > 0:
        received_messages.delete()
        print(f"   📨 Deleted {counts['received_messages']} received messages")
    
    # Clean up user notifications
    if counts['notifications'] > 0:
        user_notifications.delete()
        print(f"   🔔 Deleted {counts['notifications']} notifications")
    
    # Clean up message edit histories
    if counts['edit_histories'] > 0:
        edit_histories.delete()
        print(f"   📝 Deleted {counts['edit_histories']} message edit histories")
    
    # Clean up any message notifications that reference deleted messages
    orphaned_notifications = Notification.objects.filter(message__isnull=True)
    orphaned_count = orphaned_notifications.count()
    if orphaned_count > 0:
        orphaned_notifications.delete()
        print(f"   🧹 Cleaned up {orphaned_count} orphaned notifications")
    
    total_deleted = sum(counts.values()) + orphaned_count
    print(f"✅ User cleanup completed. Total records deleted: {total_deleted}")
    print(f"   User: {deleted_user_info['username']} ({deleted_user_info['email']})")


@receiver(pre_save, sender=Message)
def track_message_edits(sender, instance, **kwargs):
    """
    Signal handler that tracks message edits by saving the old content
    to MessageHistory before the message is updated.
    
    This signal listens for Message updates and creates a history entry
    if the message content has been changed.
    """
    # Only track edits for existing messages (not new ones)
    if instance.pk:
        try:
            # Get the original message from the database
            original_message = Message.objects.get(pk=instance.pk)
            
            # Check if the message content has been changed
            if original_message.message_body != instance.message_body:
                # Create a history entry with the old content
                MessageHistory.objects.create(
                    message=original_message,
                    old_content=original_message.message_body,
                    edited_by=instance.sender,  # Assuming the sender is editing their own message
                    edit_reason=getattr(instance, '_edit_reason', None)  # Optional edit reason
                )
                
                # Mark the message as edited
                instance.edited = True
                instance.edited_at = timezone.now()
                
        except Message.DoesNotExist:
            # Message doesn't exist yet (new message), do nothing
            pass


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
    Optional signal handler for logging message creation and edits.
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
    else:
        # Log message edits
        if instance.edited:
            print(f"✏️  Message edited:")
            print(f"   By: {instance.sender.email}")
            print(f"   Message ID: {instance.message_id}")
            print(f"   Edited at: {instance.edited_at}")


@receiver(post_save, sender=Notification)
def log_notification_creation(sender, instance, created, **kwargs):
    """
    Optional signal handler for logging notification creation.
    """
    if created:
        print(f"🔔 Notification created for {instance.user.email}: {instance.title}")


@receiver(post_save, sender=MessageHistory)
def log_message_edit_history(sender, instance, created, **kwargs):
    """
    Optional signal handler for logging message edit history creation.
    """
    if created:
        print(f"📝 Message edit history saved:")
        print(f"   Message ID: {instance.message.message_id}")
        print(f"   Edited by: {instance.edited_by.email}")
        print(f"   Old content: {instance.old_content[:50]}{'...' if len(instance.old_content) > 50 else ''}")
        print(f"   Edit timestamp: {instance.edit_timestamp}")
