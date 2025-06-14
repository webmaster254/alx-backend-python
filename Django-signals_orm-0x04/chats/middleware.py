import logging
import os
from datetime import datetime, timedelta
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseTooManyRequests
from collections import defaultdict
import json


class RequestLoggingMiddleware:
    """
    Middleware to log user requests including timestamp, user, and request path.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(settings.BASE_DIR, '')
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up logging configuration
        log_file = os.path.join(log_dir, 'requests.log')
        
        # Configure logger
        self.logger = logging.getLogger('request_logger')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler if it doesn't exist
        if not self.logger.handlers:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
    
    def __call__(self, request):
        """
        Process the request and log the required information.
        
        Args:
            request: The HTTP request object
            
        Returns:
            The response from the next middleware/view
        """
        # Get user information
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'
        
        # Log the request information
        log_message = f"{datetime.now()} - User: {user} - Path: {request.path}"
        self.logger.info(log_message)
        
        # Process the request through the rest of the middleware/view chain
        response = self.get_response(request)
        
        return response


class RestrictAccessByTimeMiddleware:
    """
    Middleware to restrict access to the messaging app during certain hours.
    Only allows access between 6PM (18:00) and 9PM (21:00).
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response
    
    def __call__(self, request):
        """
        Process the request and check if access is allowed based on current time.
        
        Args:
            request: The HTTP request object
            
        Returns:
            The response from the next middleware/view or 403 Forbidden
        """
        # Get current hour (0-23)
        current_hour = datetime.now().hour
        
        # Define allowed time range: 6PM (18:00) to 9PM (21:00)
        start_hour = 18  # 6PM
        end_hour = 21    # 9PM
        
        # Check if current time is outside allowed hours
        if current_hour < start_hour or current_hour >= end_hour:
            # Return 403 Forbidden response
            return HttpResponseForbidden(
                "<h1>403 Forbidden</h1>"
                "<p>Access to the messaging app is restricted to 6:00 PM - 9:00 PM.</p>"
                f"<p>Current time: {datetime.now().strftime('%I:%M %p')}</p>"
                "<p>Please try again during allowed hours.</p>"
            )
        
        # Process the request through the rest of the middleware/view chain
        response = self.get_response(request)
        
        return response


class OffensiveLanguageMiddleware:
    """
    Middleware to limit the number of chat messages a user can send within a time window
    based on their IP address. Limits to 5 messages per minute.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response
        # Store message counts per IP address with timestamps
        # Structure: {ip_address: [timestamp1, timestamp2, ...]}
        self.ip_message_history = {}
        
        # Rate limiting configuration
        self.max_messages = 5  # Maximum messages allowed
        self.time_window = 60  # Time window in seconds (1 minute)
    
    def __call__(self, request):
        """
        Process the request and check if the IP has exceeded the message limit.
        
        Args:
            request: The HTTP request object
            
        Returns:
            The response from the next middleware/view or 429 Too Many Requests
        """
        # Only check POST requests (assuming these are chat messages)
        if request.method == 'POST':
            # Get client IP address
            ip_address = self.get_client_ip(request)
            current_time = datetime.now()
            
            # Clean up old timestamps outside the time window
            self.cleanup_old_timestamps(ip_address, current_time)
            
            # Check if IP has exceeded the rate limit
            if ip_address in self.ip_message_history and len(self.ip_message_history[ip_address]) >= self.max_messages:
                # Return 429 Too Many Requests response
                return HttpResponseTooManyRequests(
                    content=json.dumps({
                        "error": "Rate limit exceeded",
                        "message": f"You can only send {self.max_messages} messages per minute. Please wait before sending another message.",
                        "retry_after": self.time_window,
                        "current_count": len(self.ip_message_history[ip_address])
                    }),
                    content_type="application/json"
                )
            
            # Add current timestamp to the IP's message history
            if ip_address not in self.ip_message_history:
                self.ip_message_history[ip_address] = []
            self.ip_message_history[ip_address].append(current_time)
        
        # Process the request through the rest of the middleware/view chain
        response = self.get_response(request)
        
        return response
    
    def get_client_ip(self, request):
        """
        Get the client's IP address from the request.
        
        Args:
            request: The HTTP request object
            
        Returns:
            str: The client's IP address
        """
        # Try to get IP from X-Forwarded-For header (for proxies/load balancers)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP if there are multiple
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            # Fallback to REMOTE_ADDR
            ip = request.META.get('REMOTE_ADDR')
        
        return ip
    
    def cleanup_old_timestamps(self, ip_address, current_time):
        """
        Remove timestamps that are outside the current time window.
        
        Args:
            ip_address: The IP address to clean up
            current_time: The current timestamp
        """
        cutoff_time = current_time - timedelta(seconds=self.time_window)
        
        # Filter out timestamps older than the time window
        if ip_address in self.ip_message_history:
            self.ip_message_history[ip_address] = [
                timestamp for timestamp in self.ip_message_history[ip_address]
                if timestamp > cutoff_time
            ]
        
        # Remove IP entry if no recent messages
        if ip_address in self.ip_message_history and not self.ip_message_history[ip_address]:
            del self.ip_message_history[ip_address]


class RolepermissionMiddleware:
    """
    Middleware to check user roles before allowing access to specific actions.
    Only allows admin and moderator users to access certain protected routes.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response
        
        # Define protected paths that require admin/moderator access
        self.protected_paths = [
            '/admin/',
            '/api/admin/',
            '/chats/admin/',
            '/api/conversations/delete/',
            '/api/users/ban/',
            '/api/users/promote/',
            '/api/messages/moderate/',
        ]
        
        # Define allowed roles
        self.allowed_roles = ['admin', 'moderator']
    
    def __call__(self, request):
        """
        Process the request and check if the user has the required role.
        
        Args:
            request: The HTTP request object
            
        Returns:
            The response from the next middleware/view or 403 Forbidden
        """
        # Check if the request path requires role-based access control
        if self.is_protected_path(request.path):
            # Check if user is authenticated
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return HttpResponseForbidden(
                    content=json.dumps({
                        "error": "Authentication required",
                        "message": "You must be logged in to access this resource.",
                        "required_roles": self.allowed_roles
                    }),
                    content_type="application/json"
                )
            
            # Check if user has the required role
            user_role = self.get_user_role(request.user)
            
            if user_role not in self.allowed_roles:
                return HttpResponseForbidden(
                    content=json.dumps({
                        "error": "Insufficient permissions",
                        "message": f"Access denied. This action requires {' or '.join(self.allowed_roles)} role.",
                        "current_role": user_role,
                        "required_roles": self.allowed_roles
                    }),
                    content_type="application/json"
                )
        
        # Process the request through the rest of the middleware/view chain
        response = self.get_response(request)
        
        return response
    
    def is_protected_path(self, path):
        """
        Check if the given path requires role-based protection.
        
        Args:
            path: The request path to check
            
        Returns:
            bool: True if the path is protected, False otherwise
        """
        return any(path.startswith(protected_path) for protected_path in self.protected_paths)
    
    def get_user_role(self, user):
        """
        Get the user's role from the user object.
        
        Args:
            user: The Django user object
            
        Returns:
            str: The user's role or 'user' if no specific role is found
        """
        # Check if user is a superuser (admin)
        if user.is_superuser:
            return 'admin'
        
        # Check if user is staff (could be moderator)
        if user.is_staff:
            return 'moderator'
        
        # Check for custom role field if it exists
        if hasattr(user, 'role'):
            return user.role
        
        # Check for groups-based roles
        if hasattr(user, 'groups'):
            user_groups = [group.name.lower() for group in user.groups.all()]
            
            if 'admin' in user_groups or 'administrator' in user_groups:
                return 'admin'
            elif 'moderator' in user_groups or 'mod' in user_groups:
                return 'moderator'
        
        # Default role for regular users
        return 'user'
