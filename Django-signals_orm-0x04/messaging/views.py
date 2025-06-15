from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db import transaction
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
                user_to_delete = request.user
            else:
                # For API requests, expect user_id in request body
                data = json.loads(request.body)
                user_id = data.get('user_id')
                if not user_id:
                    return JsonResponse({
                        'error': 'user_id is required for deletion'
                    }, status=400)
                
                try:
                    user_to_delete = User.objects.get(id=user_id)
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
            user_to_delete = request.user
        
        # Get user information before deletion for response
        user_info = {
            'id': user_to_delete.id,
            'username': user_to_delete.username,
            'email': user_to_delete.email
        }
        
        # Use transaction to ensure all deletions happen atomically
        with transaction.atomic():
            # Count related data before deletion for reporting
            messages_count = Message.objects.filter(sender=user_to_delete).count()
            received_messages_count = Message.objects.filter(receiver=user_to_delete).count()
            notifications_count = Notification.objects.filter(user=user_to_delete).count()
            edit_history_count = MessageHistory.objects.filter(edited_by=user_to_delete).count()
            
            # Log out the user if they're currently authenticated
            if hasattr(request, 'user') and request.user == user_to_delete:
                logout(request)
            
            # Delete the user (CASCADE relationships will handle related data)
            user_to_delete.delete()
            
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
