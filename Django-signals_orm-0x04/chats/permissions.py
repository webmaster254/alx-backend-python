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
        
        For PUT, PATCH, and DELETE requests, additional restrictions may apply.
        """
        user = request.user
        
        # Handle Conversation objects directly
        if hasattr(obj, 'participants'):
            # Basic permission check for all methods
            is_participant = obj.participants.filter(user_id=user.user_id).exists()
            
            # For unsafe methods (PUT, PATCH, DELETE), add extra validations if needed
            if request.method in ["PUT", "PATCH", "DELETE"]:
                # Only allow modifications to conversations if user is a participant
                return is_participant
                
            return is_participant
        
        # Handle Message objects by checking the associated conversation
        elif hasattr(obj, 'conversation'):
            is_participant = obj.conversation.participants.filter(user_id=user.user_id).exists()
            
            # For unsafe methods, only allow changes to messages created by the user
            if request.method in ["PUT", "PATCH", "DELETE"]:
                # Check if user is the sender of the message
                return is_participant and obj.sender.user_id == user.user_id
                
            return is_participant
        
        # Default deny if object type is unknown
        return False
