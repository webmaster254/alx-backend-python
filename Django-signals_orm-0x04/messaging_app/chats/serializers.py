from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import validate_email, RegexValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Conversation, Message
import re

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model"""
    email = serializers.EmailField(
        required=True,
        validators=[validate_email]
    )
    first_name = serializers.CharField(
        max_length=150,
        required=True,
        allow_blank=False,
        trim_whitespace=True
    )
    last_name = serializers.CharField(
        max_length=150,
        required=True,
        allow_blank=False,
        trim_whitespace=True
    )
    phone_number = serializers.CharField(
        max_length=15,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[
            RegexValidator(
                regex='^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    
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

    def validate_first_name(self, value):
        """Validate first name contains only letters and spaces"""
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError(
                'First name can only contain letters and spaces.'
            )
        return value.strip()
    
    def validate_last_name(self, value):
        """Validate last name contains only letters and spaces"""
        if not re.match(r'^[a-zA-Z\s]+$', value):
            raise serializers.ValidationError(
                'Last name can only contain letters and spaces.'
            )
        return value.strip()
    
    def validate_email(self, value):
        """Validate email is unique and properly formatted"""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'A user with this email already exists.'
            )
        return value.lower()
    
    def create(self, validated_data):
        """Create and return a new user with encrypted password"""
        try:
            password = validated_data.pop('password', None)
            user = User(**validated_data)
            if password:
                user.set_password(password)
            user.full_clean()
            user.save()
            return user
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)

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
    message_id = serializers.UUIDField(read_only=True)
    message_body = serializers.CharField(
        source='content',
        max_length=5000,
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            'blank': 'Message cannot be empty.',
            'required': 'Message is required.'
        }
    )
    
    class Meta:
        model = Message
        fields = [
            'message_id',
            'conversation',
            'sender',
            'message_body',
            'is_read',
            'read_at',
            'sent_at',
            'updated_at'
        ]
        read_only_fields = [
            'message_id',
            'sender',
            'sent_at',
            'updated_at',
            'read_at',
            'is_read'
        ]
    
    def validate_message_body(self, value):
        """Validate message body is not empty after trimming"""
        if not value.strip():
            raise serializers.ValidationError('Message cannot be empty.')
        return value.strip()
    
    def create(self, validated_data):
        """Create a new message with the current user as sender"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['sender'] = request.user
        else:
            raise serializers.ValidationError('User must be authenticated to send messages.')
            
        # Map message_body back to content for the model
        validated_data['content'] = validated_data.pop('message_body')
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for the Conversation model"""
    conversation_id = serializers.UUIDField(
        source='id',
        read_only=True
    )
    participants = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=True
    )
    group_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True
    )
    messages = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'participants',
            'created_at',
            'updated_at',
            'is_group',
            'group_name',
            'group_photo',
            'messages',
            'last_message',
            'unread_count'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']
        extra_kwargs = {
            'group_photo': {'required': False, 'allow_null': True}
        }
    
    def get_messages(self, obj):
        """Get paginated messages for the conversation"""
        request = self.context.get('request')
        if request and 'include_messages' in request.query_params:
            messages = obj.messages.all().order_by('-sent_at')[:50]  # Last 50 messages
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
