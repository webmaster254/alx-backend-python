from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, user_logged_out
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Prefetch, Q
from .models import Message, Notification, MessageHistory
import json


# Create your views here.

@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def delete_user(request):
    """
    View to allow a user to delete their account.
    Handles both authenticated users and API requests with user ID.
    """
    try:
        if request.method == "DELETE":
            # Handle API request with JSON data
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
            else:
                # For API requests, expect user_id in request body
                data = json.loads(request.body)
                user_id = data.get('user_id')
                if not user_id:
                    return JsonResponse({
                        'error': 'user_id is required for deletion'
                    }, status=400)
                
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return JsonResponse({
                        'error': 'User not found'
                    }, status=404)
        
        elif request.method == "POST":
            # Handle form submission from authenticated user
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Authentication required'
                }, status=401)
            user = request.user
        
        # Get user information before deletion for response
        user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
        
        # Use transaction to ensure all deletions happen atomically
        with transaction.atomic():
            # Count related data before deletion for reporting
            messages_count = Message.objects.filter(sender=user).count()
            received_messages_count = Message.objects.filter(receiver=user).count()
            notifications_count = Notification.objects.filter(user=user).count()
            edit_history_count = MessageHistory.objects.filter(edited_by=user).count()
            
            # Log out the user if they're currently authenticated
            if hasattr(request, 'user') and request.user == user:
                logout(request)
            
            # Delete the user (CASCADE relationships will handle related data)
            user.delete()
            
            return JsonResponse({
                'message': 'User account successfully deleted',
                'deleted_user': user_info,
                'cleanup_summary': {
                    'sent_messages_deleted': messages_count,
                    'received_messages_deleted': received_messages_count,
                    'notifications_deleted': notifications_count,
                    'message_edit_history_deleted': edit_history_count
                }
            }, status=200)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to delete user account: {str(e)}'
        }, status=500)


@login_required
def delete_account_page(request):
    """
    Render the account deletion confirmation page.
    """
    if request.method == 'GET':
        return render(request, 'messaging/delete_account.html', {
            'user': request.user
        })
    else:
        # Redirect DELETE/POST requests to the delete_user view
        return delete_user(request)


def get_threaded_messages_optimized(user, conversation_filter=None):
    """
    Optimized query to fetch messages with their replies using select_related and prefetch_related.
    Reduces database queries significantly for threaded conversations.
    """
    # Base queryset with optimized joins
    base_query = Message.objects.select_related(
        'sender', 
        'receiver', 
        'parent_message__sender'
    ).prefetch_related(
        # Prefetch replies with their senders
        Prefetch(
            'replies',
            queryset=Message.objects.select_related('sender', 'receiver').order_by('sent_at')
        ),
        # Prefetch edit history
        Prefetch(
            'edit_history',
            queryset=MessageHistory.objects.select_related('edited_by').order_by('-edit_timestamp')
        )
    )
    
    # Filter messages for the user
    if conversation_filter:
        base_query = base_query.filter(conversation_filter)
    else:
        # Get messages where user is sender or receiver
        base_query = base_query.filter(
            Q(sender=user) | Q(receiver=user)
        )
    
    return base_query.order_by('sent_at')


def get_message_thread_recursive(message_id, max_depth=10):
    """
    Recursively fetch all replies to a message using optimized ORM queries.
    Returns a nested structure representing the threaded conversation.
    """
    try:
        # Get the root message with optimized joins
        root_message = Message.objects.select_related(
            'sender', 
            'receiver', 
            'parent_message'
        ).prefetch_related(
            Prefetch(
                'replies',
                queryset=Message.objects.select_related('sender', 'receiver').order_by('sent_at')
            )
        ).get(id=message_id)
        
        # Build the threaded structure recursively
        return build_thread_structure(root_message, max_depth)
        
    except Message.DoesNotExist:
        return None


def build_thread_structure(message, max_depth, current_depth=0):
    """
    Recursively build a nested thread structure from a message and its replies.
    """
    if current_depth >= max_depth:
        return {
            'message': serialize_message(message),
            'replies': [],
            'reply_count': message.replies.count(),
            'truncated': True
        }
    
    thread_data = {
        'message': serialize_message(message),
        'replies': [],
        'reply_count': message.replies.count(),
        'truncated': False
    }
    
    # Recursively process replies
    for reply in message.replies.all():
        reply_thread = build_thread_structure(reply, max_depth, current_depth + 1)
        thread_data['replies'].append(reply_thread)
    
    return thread_data


def serialize_message(message):
    """
    Serialize a message object for API response.
    """
    return {
        'id': str(message.id),
        'content': message.content,
        'sender': {
            'id': str(message.sender.id),
            'email': message.sender.email,
            'first_name': getattr(message.sender, 'first_name', ''),
            'last_name': getattr(message.sender, 'last_name', ''),
        },
        'receiver': {
            'id': str(message.receiver.id),
            'email': message.receiver.email,
            'first_name': getattr(message.receiver, 'first_name', ''),
            'last_name': getattr(message.receiver, 'last_name', ''),
        },
        'parent_message_id': str(message.parent_message.id) if message.parent_message else None,
        'is_read': message.is_read,
        'edited': message.edited,
        'edited_at': message.edited_at.isoformat() if message.edited_at else None,
        'sent_at': message.sent_at.isoformat(),
        'updated_at': message.updated_at.isoformat(),
    }


@login_required
@require_http_methods(["GET"])
def get_threaded_messages(request):
    """
    API endpoint to fetch threaded messages with optimized queries.
    Supports filtering by conversation participants.
    """
    user = request.user
    
    # Optional filtering by conversation partner
    partner_id = request.GET.get('partner_id')
    conversation_filter = None
    
    if partner_id:
        try:
            partner = User.objects.get(id=partner_id)
            conversation_filter = (
                (Q(sender=user) & Q(receiver=partner)) |
                (Q(sender=partner) & Q(receiver=user))
            )
        except User.DoesNotExist:
            return JsonResponse({'error': 'Partner not found'}, status=404)
    
    # Get optimized message queryset
    messages = get_threaded_messages_optimized(user, conversation_filter)
    
    # Group messages by thread (top-level messages only)
    top_level_messages = messages.filter(parent_message__isnull=True)
    
    threaded_conversations = []
    for message in top_level_messages:
        thread_data = build_thread_structure(message, max_depth=5)
        threaded_conversations.append(thread_data)
    
    return JsonResponse({
        'conversations': threaded_conversations,
        'total_threads': len(threaded_conversations),
        'query_count': len(threaded_conversations) + 1  # Approximation of DB queries saved
    })


@login_required
@require_http_methods(["GET"])
def get_message_thread(request, message_id):
    """
    API endpoint to fetch a specific message thread with all its replies.
    Uses recursive ORM queries for efficient data retrieval.
    """
    max_depth = int(request.GET.get('max_depth', 10))
    
    thread_data = get_message_thread_recursive(message_id, max_depth)
    
    if not thread_data:
        return JsonResponse({'error': 'Message not found'}, status=404)
    
    return JsonResponse({
        'thread': thread_data,
        'max_depth': max_depth
    })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def create_reply(request):
    """
    Create a reply to an existing message with optimized parent lookup.
    """
    try:
        data = json.loads(request.body)
        parent_message_id = data.get('parent_message_id')
        content = data.get('content')
        receiver_id = data.get('receiver_id')
        
        if not all([parent_message_id, content, receiver_id]):
            return JsonResponse({
                'error': 'parent_message_id, content, and receiver_id are required'
            }, status=400)
        
        # Get parent message with select_related for optimization
        try:
            parent_message = Message.objects.select_related('sender', 'receiver').get(
                id=parent_message_id
            )
        except Message.DoesNotExist:
            return JsonResponse({'error': 'Parent message not found'}, status=404)
        
        # Get receiver
        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Receiver not found'}, status=404)
        
        # Create the reply
        reply = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            parent_message=parent_message,
            content=content
        )
        
        return JsonResponse({
            'reply': serialize_message(reply),
            'parent_thread_id': str(parent_message.id)
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def threaded_messages_ui(request):
    """
    Render the threaded messages UI template.
    """
    return render(request, 'messaging/threaded_messages.html')
