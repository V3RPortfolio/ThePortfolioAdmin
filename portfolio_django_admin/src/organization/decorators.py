from functools import wraps
import asyncio
from typing import List, Union
from uuid import UUID
from authentication.constants import OrganizationRoleType
from django.core.cache import cache
from django.http import JsonResponse


def is_function_async(func):
    return asyncio.iscoroutinefunction(func)


def require_org_roles(allowed_roles: Union[OrganizationRoleType, List[OrganizationRoleType]]):
    """
    Decorator to check if the requesting user has the required role in the target
    organization. The decorated view must accept an ``org_id: UUID`` path parameter.
    Retrieves the role from Django's cache (set when the user selects an
    organization). If the cache entry is missing the request is rejected,
    advising the user to select the organization first.
    Sets ``request.org_role`` to the verified role so views can use it without
    an extra DB round-trip.
    """
    if isinstance(allowed_roles, OrganizationRoleType):
        allowed_roles = [allowed_roles]

    def decorator(func):
        if is_function_async(func):
            @wraps(func)
            async def wrapper(request, org_id: UUID, *args, **kwargs):
                from organization.constants import build_cache_key

                username = request.auth.get("sub") if request.auth else None
                if not username:
                    return JsonResponse({"detail": "Authentication required"}, status=401)

                cache_key = build_cache_key(org_id, username)
                role = cache.get(cache_key)
                if role is None:
                    return JsonResponse(
                        {"detail": "Organization not selected. Please select the organization first."},
                        status=403,
                    )

                if role not in [r for r in allowed_roles]:
                    return JsonResponse(
                        {"detail": "You don't have permission to perform this action"},
                        status=403,
                    )
                request.org_role = role
                return await func(request, org_id, *args, **kwargs)
        else:
            @wraps(func)
            def wrapper(request, org_id: UUID, *args, **kwargs):
                from organization.constants import build_cache_key

                username = request.auth.get("sub") if request.auth else None
                if not username:
                    return JsonResponse({"detail": "Authentication required"}, status=401)

                cache_key = build_cache_key(org_id, username)
                role = cache.get(cache_key)
                if role is None:
                    return JsonResponse(
                        {"detail": "Organization not selected. Please select the organization first."},
                        status=403,
                    )

                if role not in [r for r in allowed_roles]:
                    return JsonResponse(
                        {"detail": "You don't have permission to perform this action"},
                        status=403,
                    )
                request.org_role = role
                return func(request, org_id, *args, **kwargs)

        return wrapper
    return decorator
