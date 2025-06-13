import logging
import os
from datetime import datetime
from django.conf import settings
from django.http import HttpResponseForbidden


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
