# Generated by Django 5.2.2 on 2025-06-15 13:34

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ['-sent_at'], 'verbose_name': 'Message', 'verbose_name_plural': 'Messages'},
        ),
        migrations.RenameField(
            model_name='message',
            old_name='content',
            new_name='message_body',
        ),
        migrations.RenameField(
            model_name='message',
            old_name='created_at',
            new_name='sent_at',
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('notification_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True, verbose_name='Notification ID')),
                ('notification_type', models.CharField(choices=[('message', 'New Message'), ('system', 'System Notification'), ('reminder', 'Reminder')], default='message', help_text='Type of notification', max_length=20)),
                ('title', models.CharField(help_text='Notification title', max_length=100)),
                ('content', models.TextField(help_text='Notification content/description')),
                ('is_read', models.BooleanField(default=False, help_text='Whether the notification has been read')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When the notification was created')),
                ('read_at', models.DateTimeField(blank=True, help_text='When the notification was read', null=True)),
                ('message', models.ForeignKey(blank=True, help_text='The message that triggered this notification (if applicable)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='chats.message')),
                ('user', models.ForeignKey(help_text='The user who will receive this notification', on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'db_table': 'notifications',
                'ordering': ['-created_at'],
            },
        ),
    ]
