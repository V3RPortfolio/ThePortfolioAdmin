from ninja import Router
from typing import List
from uuid import UUID
from organization.schemas import (
    OrganizationIn,
    OrganizationUpdateIn,
    OrganizationOut,
    OrganizationUserIn,
    OrganizationUserUpdateIn,
    OrganizationUserOut,
    ErrorMessage,
)
from organization.services import (
    create_organization,
    get_user_organizations,
    get_organization,
    update_organization,
    delete_organization,
    get_organization_user_role,
    list_organization_users,
    add_organization_user,
    update_organization_user_role,
    remove_organization_user,
    get_user_by_username,
    ORG_ADMIN_ROLES,
    ORG_MANAGEMENT_ROLES,
)
from organization.models import OrganizationRoleType

router = Router()

# Roles that an owner/admin may assign to other users
_OWNER_ASSIGNABLE_ROLES = [
    OrganizationRoleType.MANAGER.value,
    OrganizationRoleType.EDITOR.value,
    OrganizationRoleType.VIEWER.value,
]

# Roles that a manager may assign to other users
_MANAGER_ASSIGNABLE_ROLES = [
    OrganizationRoleType.EDITOR.value,
    OrganizationRoleType.VIEWER.value,
]


# ---------------------------------------------------------------------------
# Organization endpoints
# ---------------------------------------------------------------------------

@router.post("/", response={201: OrganizationOut, 400: ErrorMessage, 409: ErrorMessage})
async def create_org(request, payload: OrganizationIn):
    user = await get_user_by_username(request.auth["sub"])
    if not user:
        return 400, {"message": "User not found"}

    org, error = await create_organization(payload.name, user)
    if error == "name_taken":
        return 409, {"message": f"Organization with name '{payload.name}' already exists"}

    return 201, org


@router.get("/", response={200: List[OrganizationOut]})
async def list_orgs(request):
    user = await get_user_by_username(request.auth["sub"])
    if not user:
        return 200, []

    orgs = await get_user_organizations(user)
    return 200, orgs


@router.get("/{org_id}", response={200: OrganizationOut, 403: ErrorMessage, 404: ErrorMessage})
async def get_org(request, org_id: UUID):
    user = await get_user_by_username(request.auth["sub"])
    if not user:
        return 403, {"message": "Forbidden"}

    role = await get_organization_user_role(org_id, user)
    if not role:
        return 403, {"message": "You are not a member of this organization"}

    org = await get_organization(org_id)
    if not org:
        return 404, {"message": "Organization not found"}

    return 200, org


@router.patch(
    "/{org_id}",
    response={
        200: OrganizationOut,
        403: ErrorMessage,
        404: ErrorMessage,
        409: ErrorMessage,
    },
)
async def update_org(request, org_id: UUID, payload: OrganizationUpdateIn):
    user = await get_user_by_username(request.auth["sub"])
    if not user:
        return 403, {"message": "Forbidden"}

    role = await get_organization_user_role(org_id, user)
    if role not in ORG_ADMIN_ROLES:
        return 403, {"message": "Only owners and admins can update the organization"}

    org, error = await update_organization(org_id, payload.name)
    if error == "not_found":
        return 404, {"message": "Organization not found"}
    if error == "name_taken":
        return 409, {"message": f"Organization with name '{payload.name}' already exists"}

    return 200, org


@router.delete("/{org_id}", response={204: None, 403: ErrorMessage, 404: ErrorMessage})
async def delete_org(request, org_id: UUID):
    user = await get_user_by_username(request.auth["sub"])
    if not user:
        return 403, {"message": "Forbidden"}

    role = await get_organization_user_role(org_id, user)
    if role != OrganizationRoleType.OWNER.value:
        return 403, {"message": "Only owners can delete the organization"}

    deleted = await delete_organization(org_id)
    if not deleted:
        return 404, {"message": "Organization not found"}

    return 204, None


# ---------------------------------------------------------------------------
# Organization user endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/{org_id}/users",
    response={200: List[OrganizationUserOut], 403: ErrorMessage},
)
async def list_org_users(request, org_id: UUID):
    user = await get_user_by_username(request.auth["sub"])
    if not user:
        return 403, {"message": "Forbidden"}

    role = await get_organization_user_role(org_id, user)
    if not role:
        return 403, {"message": "You are not a member of this organization"}

    users = await list_organization_users(org_id)
    return 200, users


@router.post(
    "/{org_id}/users",
    response={
        201: OrganizationUserOut,
        400: ErrorMessage,
        403: ErrorMessage,
        404: ErrorMessage,
        409: ErrorMessage,
    },
)
async def add_org_user(request, org_id: UUID, payload: OrganizationUserIn):
    requester = await get_user_by_username(request.auth["sub"])
    if not requester:
        return 403, {"message": "Forbidden"}

    requester_role = await get_organization_user_role(org_id, requester)
    if requester_role not in ORG_MANAGEMENT_ROLES:
        return 403, {"message": "Only owners, admins, and managers can add users"}

    allowed_roles = (
        _OWNER_ASSIGNABLE_ROLES if requester_role in ORG_ADMIN_ROLES else _MANAGER_ASSIGNABLE_ROLES
    )
    if payload.role not in allowed_roles:
        return 400, {
            "message": f"You cannot assign role '{payload.role}'. Allowed roles: {allowed_roles}"
        }

    org_user, error = await add_organization_user(org_id, payload.username, payload.role)
    if error == "user_not_found":
        return 404, {"message": f"User '{payload.username}' not found"}
    if error == "org_not_found":
        return 404, {"message": "Organization not found"}
    if error == "user_already_member":
        return 409, {"message": f"User '{payload.username}' is already a member of this organization"}

    return 201, org_user


@router.patch(
    "/{org_id}/users/{username}",
    response={
        200: OrganizationUserOut,
        400: ErrorMessage,
        403: ErrorMessage,
        404: ErrorMessage,
    },
)
async def update_org_user_role(request, org_id: UUID, username: str, payload: OrganizationUserUpdateIn):
    requester = await get_user_by_username(request.auth["sub"])
    if not requester:
        return 403, {"message": "Forbidden"}

    requester_role = await get_organization_user_role(org_id, requester)
    if requester_role not in ORG_MANAGEMENT_ROLES:
        return 403, {"message": "Only owners, admins, and managers can update user roles"}

    allowed_roles = (
        _OWNER_ASSIGNABLE_ROLES if requester_role in ORG_ADMIN_ROLES else _MANAGER_ASSIGNABLE_ROLES
    )
    if payload.role not in allowed_roles:
        return 400, {
            "message": f"You cannot assign role '{payload.role}'. Allowed roles: {allowed_roles}"
        }

    org_user, error = await update_organization_user_role(org_id, username, payload.role)
    if error == "user_not_found":
        return 404, {"message": f"User '{username}' not found in this organization"}

    return 200, org_user


@router.delete(
    "/{org_id}/users/{username}",
    response={204: None, 403: ErrorMessage, 404: ErrorMessage},
)
async def remove_org_user(request, org_id: UUID, username: str):
    requester = await get_user_by_username(request.auth["sub"])
    if not requester:
        return 403, {"message": "Forbidden"}

    requester_role = await get_organization_user_role(org_id, requester)
    if requester_role not in ORG_MANAGEMENT_ROLES:
        return 403, {"message": "Only owners, admins, and managers can remove users"}

    success, error = await remove_organization_user(org_id, username)
    if error == "user_not_found":
        return 404, {"message": f"User '{username}' not found in this organization"}
    if error == "cannot_remove_admin_or_owner":
        return 403, {"message": "Cannot remove an owner or admin from the organization"}

    return 204, None
