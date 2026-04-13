from functools import wraps
import asyncio
from typing import List, Union
from uuid import UUID
from organization.models import OrganizationRoleType
from django.http import JsonResponse


def is_function_async(func):
    return asyncio.iscoroutinefunction(func)


def require_org_roles(allowed_roles: Union[OrganizationRoleType, List[OrganizationRoleType]]):
    """
    Decorator to check if the requesting user has the required role in the target
    organization. The decorated view must accept an ``org_id: UUID`` path parameter.
    """
    if isinstance(allowed_roles, OrganizationRoleType):
        allowed_roles = [allowed_roles]

    def decorator(func):
        if is_function_async(func):
            @wraps(func)
            async def wrapper(request, org_id: UUID, *args, **kwargs):
                from organization.services import get_organization_user_role, get_user_by_username

                username = request.auth.get("sub") if request.auth else None
                if not username:
                    return JsonResponse({"detail": "Authentication required"}, status=401)

                user = await get_user_by_username(username)
                if not user:
                    return JsonResponse({"detail": "User not found"}, status=401)

                role = await get_organization_user_role(org_id, user)
                if not role or role not in [r.value for r in allowed_roles]:
                    return JsonResponse(
                        {"detail": "You don't have permission to perform this action"},
                        status=403,
                    )
                return await func(request, org_id, *args, **kwargs)
        else:
            @wraps(func)
            def wrapper(request, org_id: UUID, *args, **kwargs):
                from django.contrib.auth import get_user_model
                from organization.models import OrganizationUser

                username = request.auth.get("sub") if request.auth else None
                if not username:
                    return JsonResponse({"detail": "Authentication required"}, status=401)

                User = get_user_model()
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    return JsonResponse({"detail": "User not found"}, status=401)

                try:
                    org_user = OrganizationUser.objects.get(organization_id=org_id, user=user)
                    role = org_user.role
                except OrganizationUser.DoesNotExist:
                    role = None

                if not role or role not in [r.value for r in allowed_roles]:
                    return JsonResponse(
                        {"detail": "You don't have permission to perform this action"},
                        status=403,
                    )
                return func(request, org_id, *args, **kwargs)

        return wrapper
    return decorator
