from django.contrib.auth.models import AnonymousUser, AbstractUser
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from typing import Optional
from jose import jwt
from django.conf import settings

User = get_user_model()

class AsyncAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    async def __call__(self, request):
        # Store the original request.user property
        original_user = getattr(request, '_user', None)

        # Add an async_user property to request
        request.async_user = AsyncUserProperty(request)
        
        response = await self.get_response(request)
        
        # Restore original request.user if it existed
        if original_user is not None:
            request._user = original_user

        return response

class AsyncUserProperty:
    def __init__(self, request):
        self.request = request
        self._user = None

    async def get_user_from_token(self) -> Optional[AbstractUser]:
        auth_header = self.request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            username = payload.get('sub')
            if not username:
                return None

            # Use sync_to_async to get user from database
            user = await sync_to_async(User.objects.get)(username=username)
            return user
        except (jwt.JWTError, User.DoesNotExist):
            return None

    def __get__(self, obj, objtype=None):
        return self

    async def __aiter__(self):
        user = await self.get_user_from_token()
        if user:
            yield user
        else:
            yield AnonymousUser()

    async def is_authenticated(self):
        user = await self.get_user_from_token()
        return user is not None and user.is_authenticated

    async def is_anonymous(self):
        return not await self.is_authenticated()

    async def get_username(self):
        user = await self.get_user_from_token()
        return user.username if user else None