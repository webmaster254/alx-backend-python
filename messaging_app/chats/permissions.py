from rest_framework import permissions


class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission class to allow only participants of a conversation to access,
    send, view, update, and delete messages in that conversation.
    """
    
    def has_permission(self, request, view):
        """
        Check if the user is authenticated.
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user is a participant of the conversation.
        This works for both Conversation objects and Message objects.
        """
        user = request.user
        
        # Handle Conversation objects directly
        if hasattr(obj, 'participants'):
            return obj.participants.filter(user_id=user.user_id).exists()
        
        # Handle Message objects by checking the associated conversation
        elif hasattr(obj, 'conversation'):
            return obj.conversation.participants.filter(user_id=user.user_id).exists()
        
        # Default deny if object type is unknown
        return False
