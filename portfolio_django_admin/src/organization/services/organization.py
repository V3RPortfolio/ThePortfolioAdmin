from django.contrib.auth import get_user_model
from django.core.cache import cache
from organization.models import Organization, OrganizationUser
from authentication.constants import (
    OrganizationRoleType,
    ORG_ADMIN_ROLES
)
from organization.constants import (
    OrganizationStatus,
    UserInvitationStatus
)
from asgiref.sync import sync_to_async
from typing import Optional, List, Tuple
from uuid import UUID

User = get_user_model()

CACHE_KEY_PREFIX = "org_role_cache"
CACHE_TIMEOUT = 86400  # 24 hours


def _build_cache_key(organization_id: UUID, email: str) -> str:
    return f"{CACHE_KEY_PREFIX}__{organization_id}__{email}"


@sync_to_async
def get_user_id_by_email(email: str) -> Optional[int]:
    try:
        return User.objects.values_list('id', flat=True).get(email=email)
    except User.DoesNotExist:
        return None
    
@sync_to_async
def get_user_id_by_username(username: str) -> Optional[int]:
    try:
        return User.objects.values_list('id', flat=True).get(username=username)
    except User.DoesNotExist:
        return None


@sync_to_async
def get_user_by_email(email: str):
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None


@sync_to_async
def create_organization(name: str, creator_user_id: int) -> Tuple[Optional[Organization], Optional[str]]:
    if Organization.objects.filter(name=name).exists():
        return None, "name_taken"
    org = Organization.objects.create(name=name)
    OrganizationUser.objects.create(
        organization=org,
        user_id=creator_user_id,
        role=OrganizationRoleType.OWNER.value,
        invited_by=None,
        invitation_status=UserInvitationStatus.ACCEPTED.value,
        responded_at=org.created_at
    )
    return org, None


@sync_to_async
def get_user_organizations(user_id: int) -> List[Organization]:
    return list(
        Organization.objects.filter(organization_users__user_id=user_id)
        .exclude(status=OrganizationStatus.DELETED.value)
        .order_by('name')
    )


@sync_to_async
def get_organization(org_id: UUID) -> Optional[Organization]:
    try:
        return Organization.objects.exclude(status=OrganizationStatus.DELETED.value).get(id=org_id)
    except Organization.DoesNotExist:
        return None


@sync_to_async
def update_organization(org_id: UUID, description: str) -> Tuple[Optional[Organization], Optional[str]]:
    try:
        org = Organization.objects.exclude(status=OrganizationStatus.DELETED.value).get(id=org_id)
        org.description = description
        org.save()
        return org, None
    except Organization.DoesNotExist:
        return None, "not_found"


@sync_to_async
def delete_organization(org_id: UUID) -> bool:
    try:
        org = Organization.objects.exclude(status=OrganizationStatus.DELETED.value).get(id=org_id)
        org.status = OrganizationStatus.DELETED.value
        org.save()
        return True
    except Organization.DoesNotExist:
        return False


@sync_to_async
def get_organization_user_role(org_id: UUID, user_id: int) -> Optional[str]:
    try:
        org_user = OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).get(organization_id=org_id, user_id=user_id)
        
        return org_user.role
    except OrganizationUser.DoesNotExist:
        return None


@sync_to_async
def list_organization_users(org_id: UUID) -> List[OrganizationUser]:
    return list(
        OrganizationUser.objects.filter(organization_id=org_id)
        .exclude(organization__status=OrganizationStatus.DELETED.value)
        .select_related('user')
        .order_by('created_at')
    )


@sync_to_async
def invite_organization_user(
    org_id: UUID, email: str, role: str
) -> Tuple[Optional[OrganizationUser], Optional[str]]:
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return None, "user_not_found"

    try:
        org = Organization.objects.exclude(status=OrganizationStatus.DELETED.value).get(id=org_id)
    except Organization.DoesNotExist:
        return None, "org_not_found"

    if OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).filter(organization=org, user=user).exists():
        return None, "user_already_member"

    org_user = OrganizationUser.objects.create(organization=org, user=user, role=role)
    org_user = OrganizationUser.objects.select_related('user').get(id=org_user.id)
    return org_user, None


@sync_to_async
def respond_to_organization_invite(
    org_id: UUID, user_id: int, accept: bool
) -> Tuple[Optional[OrganizationUser], Optional[str]]:
    try:
        org_user = OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).select_related('user').get(
            organization_id=org_id, user_id=user_id
        )
        if org_user.invitation_status != UserInvitationStatus.PENDING.value:
            return None, "invite_already_responded"
        org_user.invitation_status = UserInvitationStatus.ACCEPTED.value if accept else UserInvitationStatus.DECLINED.value
        org_user.save()
        return org_user, None
    except OrganizationUser.DoesNotExist:
        return None, "invite_not_found"

@sync_to_async
def update_organization_user_role(
    org_id: UUID, email: str, role: str
) -> Tuple[Optional[OrganizationUser], Optional[str]]:
    try:
        org_user = OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).select_related('user').get(
            organization_id=org_id, user__email=email, invitation_status=UserInvitationStatus.ACCEPTED.value
        )
        org_user.role = role
        org_user.save()
        cache_key = _build_cache_key(org_id, email)
        if cache.get(cache_key) is not None:
            cache.set(cache_key, role, CACHE_TIMEOUT)
        return org_user, None
    except OrganizationUser.DoesNotExist:
        return None, "user_not_found"


@sync_to_async
def remove_organization_user(
    org_id: UUID, email: str
) -> Tuple[bool, Optional[str]]:
    try:
        org_user = OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).get(
            organization_id=org_id, user__email=email
        )
        if org_user.role in ORG_ADMIN_ROLES:
            return False, "cannot_remove_admin_or_owner"
        org_user.delete()
        cache.delete(_build_cache_key(org_id, email))
        return True, None
    except OrganizationUser.DoesNotExist:
        return False, "user_not_found"


@sync_to_async
def select_organization(
    user_id: int, organization_id: UUID
) -> Tuple[Optional[str], Optional[str]]:
    try:
        org_user = OrganizationUser.objects.exclude(
            organization__status=OrganizationStatus.DELETED.value
        ).select_related('user').get(
            organization_id=organization_id, user_id=user_id
        )
    except OrganizationUser.DoesNotExist:
        return None, "user_not_in_organization"

    role = org_user.role
    email = org_user.user.email
    cache_key = _build_cache_key(organization_id, email)
    cache.set(cache_key, role, CACHE_TIMEOUT)
    return role, None
