from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from asgiref.sync import sync_to_async
from organization.models import Organization, OrganizationUser
from authentication.constants import (
    OrganizationRoleType,
    ORG_ADMIN_ROLES
)
from organization.constants import (
    OrganizationStatus,
    UserInvitationStatus,
    CACHE_TIMEOUT,
    build_cache_key,
)
from notification.tasks import publish_notification
from notification.dto import PublishUserNotificationDTO
from notification.constants import NotificationType

from typing import Optional, List, Tuple
from uuid import UUID
from datetime import timezone, datetime

User = get_user_model()



async def get_user_id_by_email(email: str) -> Optional[int]:
    try:
        return await User.objects.values_list('id', flat=True).aget(email=email)
    except User.DoesNotExist:
        return None
    
async def get_user_id_by_username(username: str) -> Optional[int]:
    try:
        return await User.objects.values_list('id', flat=True).aget(username=username)
    except User.DoesNotExist:
        return None


async def get_user_by_email(email: str) -> Optional[AbstractUser]:
    try:
        return await User.objects.aget(email=email)
    except User.DoesNotExist:
        return None

@transaction.atomic
def create_organization_sync(name: str, creator_user_id: int, description: Optional[str] = None) -> Tuple[Optional[Organization], Optional[str]]:
    if Organization.objects.filter(name=name).exists():
        return None, "The name is already taken by another organization. Please choose a different name."
    
    org = Organization.objects.create(name=name, description=description)
    OrganizationUser.objects.create(
        organization=org,
        user_id=creator_user_id,
        role=OrganizationRoleType.OWNER.value,
        invited_by=None,
        invitation_status=UserInvitationStatus.ACCEPTED.value,
        responded_at=org.created_at
    )
    return org, None

async def create_organization(name: str, creator_user_id: int, description:Optional[str]=None) -> Tuple[Optional[Organization], Optional[str]]:
    return await sync_to_async(create_organization_sync)(name, creator_user_id, description)


async def get_user_organizations(user_id: int) -> List[QuerySet[Organization]]:
    return Organization.objects.filter(
        organization_users__user_id=user_id,
        organization_users__invitation_status=UserInvitationStatus.ACCEPTED.value
        ).exclude(status=OrganizationStatus.DELETED.value).order_by('name')



async def get_organization(org_id: UUID) -> Optional[Organization]:
    try:
        return await Organization.objects.exclude(status=OrganizationStatus.DELETED.value).aget(id=org_id)
    except Organization.DoesNotExist:
        return None



async def update_organization(org_id: UUID, description: str, updated_by_username:str) -> Tuple[Optional[Organization], Optional[str]]:
    try:
        org = await Organization.objects.exclude(status=OrganizationStatus.DELETED.value).aget(id=org_id)
        org.description = description
        org.updated_by = updated_by_username
        org.updated_at = datetime.now(timezone.utc)
        await org.asave()

        org_owner = await OrganizationUser.objects.filter(organization=org, role=OrganizationRoleType.OWNER.value).select_related('user').afirst()
        if org_owner:
            publish_notification.delay(
                PublishUserNotificationDTO(
                    user_id=org_owner.user.id,
                    description=f"Information of your organization {org.name} has been updated by {updated_by_username}.",
                    title="Organization Information Updated",
                    notification_type=NotificationType.ALERT.value
                ).model_dump()
            )
        return org, None
    except Organization.DoesNotExist:
        return None, "The organization does not exist or has been deleted."



async def delete_organization(org_id: UUID) -> bool:
    try:
        org_members = OrganizationUser.objects.filter(organization_id=org_id).select_related('user')
        org = await Organization.objects.exclude(status=OrganizationStatus.DELETED.value).aget(id=org_id)
        org.status = OrganizationStatus.DELETED.value
        await org.asave()

        if await org_members.acount() > 0:    
            async for member in org_members:
                publish_notification.delay(
                    PublishUserNotificationDTO(
                        user_id=member.user.id,
                        description=f"Organization {org.name} has been deleted.",
                        title="Organization Deleted",
                        notification_type=NotificationType.ALERT.value
                    ).model_dump()
                )
                cache_key = build_cache_key(org_id, member.user.username)
                cache.delete(cache_key)
        return True
    except Organization.DoesNotExist:
        return False


async def get_organization_user_role(org_id: UUID, user_id: int) -> Optional[str]:
    try:
        org_user = await OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).aget(organization_id=org_id, user_id=user_id, invitation_status=UserInvitationStatus.ACCEPTED.value)
        
        return org_user.role
    except OrganizationUser.DoesNotExist:
        return None



async def list_organization_users(org_id: UUID) -> QuerySet[OrganizationUser]:
    return OrganizationUser.objects.filter(organization_id=org_id).exclude(
        organization__status=OrganizationStatus.DELETED.value).select_related('user').order_by('created_at')
    

async def update_organization_user_role(
    org_id: UUID, email: str, role: str
) -> Tuple[Optional[OrganizationUser], Optional[str]]:
    try:
        org_user = await OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).select_related('user').aget(
            organization_id=org_id, user__email=email, invitation_status=UserInvitationStatus.ACCEPTED.value
        )
        org_user.role = role
        await org_user.asave()
        cache_key = build_cache_key(org_id, org_user.user.username)
        if cache.get(cache_key) is not None:
            cache.set(cache_key, role, CACHE_TIMEOUT)

        return org_user, None
    except OrganizationUser.DoesNotExist:
        return None, "The user is not a member of the organization or has not accepted the invitation."


async def remove_organization_user(
    org_id: UUID, email: str
) -> Tuple[bool, Optional[str]]:
    try:
        org_user = await OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).select_related('user').aget(
            organization_id=org_id, user__email=email
        )
        if org_user.role in ORG_ADMIN_ROLES:
            return False, "The user with admin role cannot be removed. Please transfer ownership or change the user's role before removing."
        username = org_user.user.username
        await org_user.adelete()
        cache.delete(build_cache_key(org_id, username))
        return True, None
    except OrganizationUser.DoesNotExist:
        return False, "The user is not a member of the organization or has been deleted."
    

async def leave_organization(org_id: UUID, user_id: int) -> Tuple[bool, Optional[str]]:
    try:
        org_user = await OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).select_related('user', 'organization').aget(
            organization_id=org_id, user_id=user_id
        )
        if org_user.role in ORG_ADMIN_ROLES:
            return False, "The owner cannot leave the organization. Please transfer ownership before leaving or delete the organization."
        
        username = org_user.user.username
        await org_user.adelete()
        cache.delete(build_cache_key(org_id, username))

        org_members = OrganizationUser.objects.filter(organization_id=org_id).select_related('user')
        async for member in org_members:
            publish_notification.delay(
                PublishUserNotificationDTO(
                    user_id=member.user.id,
                    description=f"{org_user.user.email} has left the organization {org_user.organization.name}.",
                    title="Organization Member Left",
                    notification_type=NotificationType.ALERT.value
                ).model_dump()
            )
        return True, None
    except OrganizationUser.DoesNotExist:
        return False, "The user is not a member of the organization or has been deleted."



async def select_organization(
    user_id: int, organization_id: UUID
) -> Tuple[Optional[str], Optional[str]]:
    try:
        org_user = await OrganizationUser.objects.exclude(
            organization__status=OrganizationStatus.DELETED.value
        ).select_related('user').aget(
            organization_id=organization_id, user_id=user_id
        )
    except OrganizationUser.DoesNotExist:
        return None, "user_not_in_organization"

    role = org_user.role
    username = org_user.user.username
    cache_key = build_cache_key(organization_id, username)
    cache.set(cache_key, role, CACHE_TIMEOUT)
    return role, None
