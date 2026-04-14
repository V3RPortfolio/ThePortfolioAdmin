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
    First checks Django's cache for the role. On cache miss, falls back to a
    database lookup via ``get_organization_user_role``. If the role is valid and
    was not cached, calls ``select_organization`` to populate the cache for
    subsequent requests.
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
                from organization.services.organization import (
                    get_user_id_by_username,
                    get_organization_user_role,
                    select_organization,
                )

                username = request.auth.get("sub") if request.auth else None
                if not username:
                    return JsonResponse({"detail": "Authentication required"}, status=401)

                cache_key = build_cache_key(org_id, username)
                role = cache.get(cache_key)
                cache_miss = role is None

                if cache_miss:
                    user_id = await get_user_id_by_username(username)
                    if user_id is None:
                        return JsonResponse(
                            {"detail": "User not found"},
                            status=403,
                        )
                    role = await get_organization_user_role(org_id, user_id)
                    if role is None:
                        return JsonResponse(
                            {"detail": "You are not a member of this organization"},
                            status=403,
                        )

                if role not in [r for r in allowed_roles]:
                    return JsonResponse(
                        {"detail": "You don't have permission to perform this action"},
                        status=403,
                    )

                if cache_miss:
                    await select_organization(user_id, org_id)

                request.org_role = role
                return await func(request, org_id, *args, **kwargs)
        else:
            @wraps(func)
            def wrapper(request, org_id: UUID, *args, **kwargs):
                from organization.constants import build_cache_key
                from organization.services.organization import (
                    get_user_id_by_username,
                    get_organization_user_role,
                    select_organization,
                )
                from asgiref.sync import async_to_sync

                username = request.auth.get("sub") if request.auth else None
                if not username:
                    return JsonResponse({"detail": "Authentication required"}, status=401)

                cache_key = build_cache_key(org_id, username)
                role = cache.get(cache_key)
                cache_miss = role is None

                if cache_miss:
                    user_id = async_to_sync(get_user_id_by_username)(username)
                    if user_id is None:
                        return JsonResponse(
                            {"detail": "User not found"},
                            status=403,
                        )
                    role = async_to_sync(get_organization_user_role)(org_id, user_id)
                    if role is None:
                        return JsonResponse(
                            {"detail": "You are not a member of this organization"},
                            status=403,
                        )

                if role not in [r for r in allowed_roles]:
                    return JsonResponse(
                        {"detail": "You don't have permission to perform this action"},
                        status=403,
                    )

                if cache_miss:
                    async_to_sync(select_organization)(user_id, org_id)

                request.org_role = role
                return func(request, org_id, *args, **kwargs)

        return wrapper
    return decorator
