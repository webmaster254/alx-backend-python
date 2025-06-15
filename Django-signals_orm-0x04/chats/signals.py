"""
Django signals for automatic notification creation when messages are sent.
"""
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Message,  User


@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """
    Signal handler that performs comprehensive cleanup when a user is deleted.
    
    This signal ensures all related data is properly cleaned up when a user
    account is deleted, maintaining data integrity and preventing orphaned records.
    """
    deleted_user_info = {
        'id': instance.user_id,
        'username': getattr(instance, 'username', 'Unknown'),
        'email': getattr(instance, 'email', 'Unknown')
    }
    
    print(f"🗑️  User deletion cleanup initiated for: {deleted_user_info}")
    
    # Count related data before cleanup for logging
    sent_messages = Message.objects.filter(sender=instance)
    user_notifications = Notification.objects.filter(user=instance)
    edit_histories = MessageHistory.objects.filter(edited_by=instance)
    
    # Get conversations where user was a participant
    user_conversations = instance.conversations.all()
    
    counts = {
        'sent_messages': sent_messages.count(),
        'notifications': user_notifications.count(),
        'edit_histories': edit_histories.count(),
        'conversations': user_conversations.count()
    }
    
    # Manual cleanup for any data that might not be handled by CASCADE
    # Note: Django's CASCADE should handle most of this, but we're being explicit
    
    # Clean up messages sent by the user (CASCADE will handle this, but logging)
    if counts['sent_messages'] > 0:
        print(f"   📧 Will cascade delete {counts['sent_messages']} sent messages")
    
    # Clean up user notifications
    if counts['notifications'] > 0:
        user_notifications.delete()
        print(f"   🔔 Deleted {counts['notifications']} notifications")
    
    # Clean up message edit histories
    if counts['edit_histories'] > 0:
        edit_histories.delete()
        print(f"   📝 Deleted {counts['edit_histories']} message edit histories")
    
    # Remove user from conversations (many-to-many relationship)
    if counts['conversations'] > 0:
        for conversation in user_conversations:
            conversation.participants.remove(instance)
        print(f"   💬 Removed user from {counts['conversations']} conversations")
    
    # Clean up any orphaned notifications that reference deleted messages
    orphaned_notifications = Notification.objects.filter(message__isnull=True)
    orphaned_count = orphaned_notifications.count()
    if orphaned_count > 0:
        orphaned_notifications.delete()
        print(f"   🧹 Cleaned up {orphaned_count} orphaned notifications")
    
    total_cleaned = sum(counts.values()) + orphaned_count
    print(f"✅ User cleanup completed. Total records cleaned: {total_cleaned}")
    print(f"   User: {deleted_user_info['username']} ({deleted_user_info['email']})")