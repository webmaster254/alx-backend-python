import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator


class UserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier"""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        
        # Set default first_name and last_name if not provided
        if 'first_name' not in extra_fields:
            extra_fields['first_name'] = 'Admin'
        if 'last_name' not in extra_fields:
            extra_fields['last_name'] = 'User'

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model that extends AbstractUser"""
    user_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    username = None
    email = models.EmailField(
        unique=True,
        verbose_name='email address'
    )
    first_name = models.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z\s]*$',
                message='First name can only contain letters and spaces.',
                code='invalid_first_name'
            )
        ]
    )
    last_name = models.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z\s]*$',
                message='Last name can only contain letters and spaces.',
                code='invalid_last_name'
            )
        ]
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex='^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True,
        help_text='Upload a profile picture'
    )
    is_verified = models.BooleanField(
        default=False,
        help_text='Designates whether the user has verified their email address.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class Conversation(models.Model):
    """Model representing a conversation between users"""
    conversation_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='Conversation ID'
    )
    participants = models.ManyToManyField(
        User,
        related_name='conversations',
        help_text='Users participating in this conversation'
    )
    is_group = models.BooleanField(
        default=False,
        help_text='Whether this is a group conversation or direct message'
    )
    group_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Name of the group (only for group conversations)'
    )
    group_photo = models.ImageField(
        upload_to='group_photos/',
        null=True,
        blank=True,
        help_text='Optional photo for group conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'

    def __str__(self):
        if self.is_group:
            return f"Group: {self.group_name}"
        participants = self.participants.all()[:2]
        return " - ".join([user.email for user in participants])


class Message(models.Model):
    """Model representing a message in a conversation"""
    message_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='Message ID'
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        db_column='conversation_id',
        to_field='conversation_id',
        help_text='The conversation this message belongs to'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text='The user who sent this message'
    )
    message_body = models.TextField(
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
    sent_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    edited = models.BooleanField(
        default=False,
        help_text='Whether this message has been edited'
    )
    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the message was last edited'
    )
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

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

    def __str__(self):
        return f"{self.sender.email} in {self.conversation}: {self.message_body[:50]}"



