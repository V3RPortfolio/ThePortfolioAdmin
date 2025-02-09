from django.contrib.auth.models import AnonymousUser, AbstractUser
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from typing import Optional
from jose import jwt
from django.conf import settings
from authentication.models import UserRole

User = get_user_model()

class AuthorizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.headers.get("Authorization", "")
        request.roles = []
        if not token:
            request.user = AnonymousUser()
            return self.get_response(request)
        token = token.split("Bearer ")[-1]
        if not token:
            request.user = AnonymousUser()
            return self.get_response(request)
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user = self.get_user(payload.get("sub"))
            request.user = user
            request.roles = [role.role for role in UserRole.objects.filter(user=user)]
        except Exception as e:
            request.user = AnonymousUser()
        return self.get_response(request)

    def get_user(self, username:str)->Optional[AbstractUser]:
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            return None