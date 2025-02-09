# authentication/decorators.py
from functools import wraps
from typing import List, Union
from authentication.models import RoleType
from django.http import JsonResponse

def require_roles(allowed_roles: Union[RoleType, List[RoleType]]):
    if isinstance(allowed_roles, RoleType):
        allowed_roles = [allowed_roles]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            # Get roles from JWT token
            user_roles = request.auth.get("roles", []) if request.auth else []
            
            # Check if user has any of the required roles
            if not any(role in [r.value for r in allowed_roles] for role in user_roles):
                return JsonResponse(
                    {"detail": "You don't have permission to perform this action"},
                    status=403
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# For GraphQL implementation
def require_graphql_roles(allowed_roles: Union[RoleType, List[RoleType]]):
    if isinstance(allowed_roles, RoleType):
        allowed_roles = [allowed_roles]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(root, info, *args, **kwargs):
            # Get roles from context (passed from middleware)
            user_roles = info.context.get("roles", []) if info.context else []
            
            # Check if user has any of the required roles
            if not any(role in [r.value for r in allowed_roles] for role in user_roles):
                raise Exception("You don't have permission to perform this action")
            return await func(root, info, *args, **kwargs)
        return wrapper
    return decorator
