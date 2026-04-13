from django.contrib.auth import get_user_model
from organization.models import Organization, OrganizationUser, OrganizationRoleType
from asgiref.sync import sync_to_async
from typing import Optional, List, Tuple
from uuid import UUID

User = get_user_model()

ORG_ADMIN_ROLES = [OrganizationRoleType.OWNER.value, OrganizationRoleType.ADMIN.value]
ORG_MANAGEMENT_ROLES = [
    OrganizationRoleType.OWNER.value,
    OrganizationRoleType.ADMIN.value,
    OrganizationRoleType.MANAGER.value,
]
VALID_ROLES = [role.value for role in OrganizationRoleType]


@sync_to_async
def get_user_by_username(username: str):
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None


@sync_to_async
def create_organization(name: str, creator_user) -> Tuple[Optional[Organization], Optional[str]]:
    if Organization.objects.filter(name=name).exists():
        return None, "name_taken"
    org = Organization.objects.create(name=name)
    OrganizationUser.objects.create(
        organization=org,
        user=creator_user,
        role=OrganizationRoleType.OWNER.value,
    )
    return org, None


@sync_to_async
def get_user_organizations(user) -> List[Organization]:
    return list(
        Organization.objects.filter(organization_users__user=user).order_by('name')
    )


@sync_to_async
def get_organization(org_id: UUID) -> Optional[Organization]:
    try:
        return Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return None


@sync_to_async
def update_organization(org_id: UUID, name: str) -> Tuple[Optional[Organization], Optional[str]]:
    if Organization.objects.filter(name=name).exclude(id=org_id).exists():
        return None, "name_taken"
    try:
        org = Organization.objects.get(id=org_id)
        org.name = name
        org.save()
        return org, None
    except Organization.DoesNotExist:
        return None, "not_found"


@sync_to_async
def delete_organization(org_id: UUID) -> bool:
    try:
        org = Organization.objects.get(id=org_id)
        org.delete()
        return True
    except Organization.DoesNotExist:
        return False


@sync_to_async
def get_organization_user_role(org_id: UUID, user) -> Optional[str]:
    try:
        org_user = OrganizationUser.objects.get(organization_id=org_id, user=user)
        return org_user.role
    except OrganizationUser.DoesNotExist:
        return None


@sync_to_async
def list_organization_users(org_id: UUID) -> List[OrganizationUser]:
    return list(
        OrganizationUser.objects.filter(organization_id=org_id)
        .select_related('user')
        .order_by('created_at')
    )


@sync_to_async
def add_organization_user(
    org_id: UUID, username: str, role: str
) -> Tuple[Optional[OrganizationUser], Optional[str]]:
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return None, "user_not_found"

    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return None, "org_not_found"

    if OrganizationUser.objects.filter(organization=org, user=user).exists():
        return None, "user_already_member"

    org_user = OrganizationUser.objects.create(organization=org, user=user, role=role)
    org_user = OrganizationUser.objects.select_related('user').get(id=org_user.id)
    return org_user, None


@sync_to_async
def update_organization_user_role(
    org_id: UUID, username: str, role: str
) -> Tuple[Optional[OrganizationUser], Optional[str]]:
    try:
        org_user = OrganizationUser.objects.select_related('user').get(
            organization_id=org_id, user__username=username
        )
        org_user.role = role
        org_user.save()
        return org_user, None
    except OrganizationUser.DoesNotExist:
        return None, "user_not_found"


@sync_to_async
def remove_organization_user(
    org_id: UUID, username: str
) -> Tuple[bool, Optional[str]]:
    try:
        org_user = OrganizationUser.objects.get(
            organization_id=org_id, user__username=username
        )
        if org_user.role in ORG_ADMIN_ROLES:
            return False, "cannot_remove_admin_or_owner"
        org_user.delete()
        return True, None
    except OrganizationUser.DoesNotExist:
        return False, "user_not_found"
