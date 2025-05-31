from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model"""
    class Meta:
        model = User
        fields = [
            'id', 
            'email', 
            'first_name', 
            'last_name',
            'phone_number',
            'bio',
            'birth_date',
            'profile_picture',
            'date_joined',
            'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True},
            'profile_picture': {'required': False, 'allow_null': True}
        }

    def create(self, validated_data):
        """Create and return a new user with encrypted password"""
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """Update a user, setting the password correctly if provided"""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for the Message model"""
    sender = UserSerializer(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='sender',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'sender_id',
            'conversation',
            'content',
            'timestamp',
            'is_read',
            'read_at'
        ]
        read_only_fields = ['id', 'timestamp', 'is_read', 'read_at', 'sender']

    def create(self, validated_data):
        # Automatically set the sender to the current user if not provided
        if 'sender' not in validated_data and 'request' in self.context:
            validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for the Conversation model"""
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='participants',
        many=True,
        write_only=True,
        required=False
    )
    messages = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'participants',
            'participant_ids',
            'created_at',
            'updated_at',
            'is_group',
            'group_name',
            'group_description',
            'messages',
            'last_message',
            'unread_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'messages', 'last_message', 'unread_count']

    def get_messages(self, obj):
        """Return paginated messages for the conversation"""
        request = self.context.get('request')
        if request and 'include_messages' in request.query_params:
            messages = obj.messages.all().order_by('-timestamp')[:50]  # Get last 50 messages
            return MessageSerializer(messages, many=True, context=self.context).data
        return []

    def get_last_message(self, obj):
        """Return the last message in the conversation"""
        last_message = obj.messages.order_by('-timestamp').first()
        if last_message:
            return MessageSerializer(last_message, context=self.context).data
        return None

    def get_unread_count(self, obj):
        """Return count of unread messages for the current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0

    def create(self, validated_data):
        """Create a new conversation with participants"""
        participants = validated_data.pop('participants', [])
        conversation = Conversation.objects.create(**validated_data)
        conversation.participants.set(participants)
        return conversation

    def update(self, instance, validated_data):
        """Update conversation, including participants"""
        participants = validated_data.pop('participants', None)
        if participants is not None:
            instance.participants.set(participants)
        return super().update(instance, validated_data)
