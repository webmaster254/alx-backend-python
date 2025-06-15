import django_filters
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Message, Conversation

User = get_user_model()


class MessageFilter(django_filters.FilterSet):
    """
    Filter for Message model to allow filtering by various parameters.
    """
    # Time range filters
    sent_after = django_filters.DateTimeFilter(field_name='sent_at', lookup_expr='gte')
    sent_before = django_filters.DateTimeFilter(field_name='sent_at', lookup_expr='lte')
    sent_date = django_filters.DateFilter(field_name='sent_at', lookup_expr='date')
    
    # Content filter
    content = django_filters.CharFilter(field_name='message_body', lookup_expr='icontains')
    
    # Read status
    is_read = django_filters.BooleanFilter(field_name='is_read')
    
    # Sender filter (can filter by email or ID)
    sender_email = django_filters.CharFilter(field_name='sender__email', lookup_expr='iexact')
    sender = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    
    # Conversation filter
    conversation = django_filters.ModelChoiceFilter(queryset=Conversation.objects.all())
    
    class Meta:
        model = Message
        fields = [
            'conversation', 
            'sender', 
            'sender_email',
            'is_read', 
            'sent_after', 
            'sent_before', 
            'sent_date',
            'content'
        ]


class ConversationFilter(django_filters.FilterSet):
    """
    Filter for Conversation model.
    """
    # Filter for group or direct messages
    is_group = django_filters.BooleanFilter(field_name='is_group')
    
    # Filter by group name (for group conversations)
    group_name = django_filters.CharFilter(field_name='group_name', lookup_expr='icontains')
    
    # Filter by participant (any participant in the conversation)
    participant = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        method='filter_by_participant'
    )
    
    # Filter by participant email
    participant_email = django_filters.CharFilter(method='filter_by_email')
    
    # Filter by creation date
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Filter by last update date
    updated_after = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    class Meta:
        model = Conversation
        fields = [
            'is_group', 
            'group_name', 
            'participant',
            'participant_email',
            'created_after',
            'created_before',
            'updated_after',
            'updated_before',
        ]
    
    def filter_by_participant(self, queryset, name, value):
        """Filter conversations by participant."""
        if value:
            return queryset.filter(participants=value)
        return queryset
    
    def filter_by_email(self, queryset, name, value):
        """Filter conversations by participant email."""
        if value:
            try:
                return queryset.filter(participants__email__iexact=value)
            except Exception:
                return queryset.none()
        return queryset
