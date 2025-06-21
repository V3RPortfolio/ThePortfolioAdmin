# authentication/decorators.py
from functools import wraps
import asyncio
from typing import List, Union
from authentication.models import RoleType
from authentication.schemas import DeviceTokenPayload
from django.http import JsonResponse
from authentication.services.auth import verify_device_token
from datetime import datetime
from django.conf import settings
from asgiref.sync import sync_to_async



def is_function_async(func):
    return asyncio.iscoroutinefunction(func)

def require_roles(allowed_roles: Union[RoleType, List[RoleType]]):
    if isinstance(allowed_roles, RoleType):
        allowed_roles = [allowed_roles]
    
    def decorator(func):
        if is_function_async(func):
            @wraps(func)
            async def wrapper(request, *args, **kwargs):
                # Get roles from JWT token
                user_roles = request.roles or []
                
                # Check if user has any of the required roles
                if not any(role in [r.value for r in allowed_roles] for role in user_roles):
                    return JsonResponse(
                        {"detail": "You don't have permission to perform this action"},
                        status=403
                    )
                return await func(request, *args, **kwargs)
        else:
            @wraps(func)
            def wrapper(request, *args, **kwargs):
                # Get roles from JWT token
                user_roles = request.roles or []
                
                if not any(role in [r.value for r in allowed_roles] for role in user_roles):
                    return JsonResponse(
                        {"detail": "You don't have permission to perform this action"},
                        status=403
                    )
                return func(request, *args, **kwargs)
            
        return wrapper
    return decorator




# For GraphQL implementation
def require_graphql_roles(allowed_roles: Union[RoleType, List[RoleType]]):
    if isinstance(allowed_roles, RoleType):
        allowed_roles = [allowed_roles]
    
    def decorator(func):
        if is_function_async(func):
            @wraps(func)
            async def wrapper(root, info, *args, **kwargs):
                # Get roles from context (passed from middleware)
                try:
                    if not info.context or not info.context.request:
                        raise Exception("No context found")
                    user_roles = info.context.request.roles or []
                except:
                    user_roles = []
                
                # Check if user has any of the required roles
                if not any(role in [r.value for r in allowed_roles] for role in user_roles):
                    raise Exception("You don't have permission to perform this action")
                return await func(root, info, *args, **kwargs)  
        else:
            @wraps(func)
            def wrapper(root, info, *args, **kwargs):
                # Get roles from context (passed from middleware)
                try:
                    if not info.context or not info.context.request:
                        raise Exception("No context found")
                    user_roles = info.context.request.roles or []
                except:
                    user_roles = []
                
                # Check if user has any of the required roles
                if not any(role in [r.value for r in allowed_roles] for role in user_roles):
                    raise Exception("You don't have permission to perform this action")
                return func(root, info, *args, **kwargs)
            
            return wrapper
    return decorator

def require_device_token():
    def decorator(func):
        if is_function_async(func):
            @wraps(func)
            async def wrapper(request, *args, **kwargs):
                device_token = request.headers.get(settings.DEVICE_TOKEN_HEADER)
                
                if not device_token:
                    return JsonResponse(
                        {"detail": "Device token is required"},
                        status=401
                    )
                
                # Verify the device token using the auth service
                device_payload = verify_device_token(device_token)
                
                if not device_payload:
                    return JsonResponse(
                        {"detail": "Invalid device token"},
                        status=401
                    )
                
                # Check if token has expired
                expiration = datetime.fromtimestamp(device_payload.get("exp", 0))
                if datetime.utcnow() > expiration:
                    return JsonResponse(
                        {"detail": "Device token has expired"},
                        status=401
                    )
                
                # Add verified device info to request for use in the endpoint
                request.device_info = DeviceTokenPayload(**device_payload).model_dump()
                
                return await func(request, *args, **kwargs)
        else:
            @wraps(func)
            def wrapper(request, *args, **kwargs):
                device_token = request.headers.get(settings.DEVICE_TOKEN_HEADER)
                
                if not device_token:
                    return JsonResponse(
                        {"detail": "Device token is required"},
                        status=401
                    )
                
                device_payload = verify_device_token(device_token)
                
                if not device_payload:
                    return JsonResponse(
                        {"detail": "Invalid device token"},
                        status=401
                    )
                
                # Add verified device info to request for use in the endpoint
                request.device_info = DeviceTokenPayload(**device_payload).model_dump()

                expiration = datetime.fromtimestamp(device_payload.get("exp", 0))
                if datetime.utcnow() > expiration:
                    return JsonResponse(
                        {"detail": "Device token has expired"},
                        status=401
                    )
                
                request.device_info = DeviceTokenPayload(**device_payload).model_dump()
                
                return func(request, *args, **kwargs)
                

        return wrapper
    return decorator
