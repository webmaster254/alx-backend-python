from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from datetime import datetime


User = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that extends the default JWT authentication
    with additional functionality such as logging and verification.
    """
    
    def authenticate(self, request):
        """
        Extend the authenticate method to add additional verification and logging.
        """
        # Call the parent authenticate method
        authenticated = super().authenticate(request)
        
        # If authentication failed, return None
        if authenticated is None:
            return None
            
        user, token = authenticated
        
        # Record the last login time (optional)
        user.last_login = datetime.now()
        user.save(update_fields=['last_login'])
        
        return user, token


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that adds additional user information 
    to the token response
    """
    
    @classmethod
    def get_token(cls, user):
        # Get the token from the parent class
        token = super().get_token(user)
        
        # Add custom claims
        token['user_id'] = str(user.user_id)
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        
        return token
    
    def validate(self, attrs):
        # The original validate method returns access, refresh tokens
        data = super().validate(attrs)
        
        # Add additional information about the user
        data['user_id'] = str(self.user.user_id)
        data['email'] = self.user.email
        data['first_name'] = self.user.first_name
        data['last_name'] = self.user.last_name
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that uses our CustomTokenObtainPairSerializer
    """
    serializer_class = CustomTokenObtainPairSerializer


class EmailOrUserIdAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication to allow authentication with email or user_id
    in addition to the default username field
    """
    
    def authenticate(self, request):
        # Get the credentials from the request
        email_or_id = request.data.get('username', None)
        password = request.data.get('password', None)
        
        if not email_or_id or not password:
            return None
            
        # Try to find a user that matches the provided credential
        try:
            # First try with email
            user = User.objects.filter(email=email_or_id).first()
            
            # If no user found, try with user_id
            if user is None:
                user = User.objects.filter(user_id=email_or_id).first()
                
            if user is None:
                # No user was found with the provided credentials
                return None
                
            # Verify the password
            if user.check_password(password):
                return (user, None)
            else:
                return None
                
        except User.DoesNotExist:
            return None
