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
    get_user_id_by_email,
    create_organization,
    get_user_organizations,
    get_organization,
    update_organization,
    delete_organization,
    list_organization_users,
    add_organization_user,
    update_organization_user_role,
    remove_organization_user,
    ORG_ADMIN_ROLES,
)
from organization.constants import (
    OrganizationRoleType,
    ORG_MANAGEMENT_ROLES,
    OWNER_ASSIGNABLE_ROLES,
    MANAGER_ASSIGNABLE_ROLES,
)
from organization.decorators import require_org_roles

router = Router()


# ---------------------------------------------------------------------------
# Organization endpoints
# ---------------------------------------------------------------------------

@router.post("/", response={201: OrganizationOut, 400: ErrorMessage, 409: ErrorMessage})
async def create_org(request, payload: OrganizationIn):
    user_id = await get_user_id_by_email(request.auth["sub"])
    if not user_id:
        return 400, {"message": "User not found"}

    org, error = await create_organization(payload.name, user_id)
    if error == "name_taken":
        return 409, {"message": f"Organization with name '{payload.name}' already exists"}

    return 201, org


@router.get("/", response={200: List[OrganizationOut]})
async def list_orgs(request):
    user_id = await get_user_id_by_email(request.auth["sub"])
    if not user_id:
        return 200, []

    orgs = await get_user_organizations(user_id)
    return 200, orgs


@router.get("/{org_id}", response={200: OrganizationOut, 403: ErrorMessage, 404: ErrorMessage})
@require_org_roles(list(OrganizationRoleType))
async def get_org(request, org_id: UUID):
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
@require_org_roles(ORG_ADMIN_ROLES)
async def update_org(request, org_id: UUID, payload: OrganizationUpdateIn):
    org, error = await update_organization(org_id, payload.name)
    if error == "not_found":
        return 404, {"message": "Organization not found"}
    if error == "name_taken":
        return 409, {"message": f"Organization with name '{payload.name}' already exists"}

    return 200, org


@router.delete("/{org_id}", response={204: None, 403: ErrorMessage, 404: ErrorMessage})
@require_org_roles([OrganizationRoleType.OWNER])
async def delete_org(request, org_id: UUID):
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
@require_org_roles(list(OrganizationRoleType))
async def list_org_users(request, org_id: UUID):
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
@require_org_roles(ORG_MANAGEMENT_ROLES)
async def add_org_user(request, org_id: UUID, payload: OrganizationUserIn):
    requester_role = request.org_role
    allowed_roles = (
        OWNER_ASSIGNABLE_ROLES if requester_role in ORG_ADMIN_ROLES else MANAGER_ASSIGNABLE_ROLES
    )
    if payload.role not in allowed_roles:
        return 400, {
            "message": f"You cannot assign role '{payload.role}'. Allowed roles: {allowed_roles}"
        }

    org_user, error = await add_organization_user(org_id, payload.email, payload.role)
    if error == "user_not_found":
        return 404, {"message": f"User '{payload.email}' not found"}
    if error == "org_not_found":
        return 404, {"message": "Organization not found"}
    if error == "user_already_member":
        return 409, {"message": f"User '{payload.email}' is already a member of this organization"}

    return 201, org_user


@router.patch(
    "/{org_id}/users/{user_email}",
    response={
        200: OrganizationUserOut,
        400: ErrorMessage,
        403: ErrorMessage,
        404: ErrorMessage,
    },
)
@require_org_roles(ORG_MANAGEMENT_ROLES)
async def update_org_user_role(request, org_id: UUID, user_email: str, payload: OrganizationUserUpdateIn):
    requester_role = request.org_role
    allowed_roles = (
        OWNER_ASSIGNABLE_ROLES if requester_role in ORG_ADMIN_ROLES else MANAGER_ASSIGNABLE_ROLES
    )
    if payload.role not in allowed_roles:
        return 400, {
            "message": f"You cannot assign role '{payload.role}'. Allowed roles: {allowed_roles}"
        }

    org_user, error = await update_organization_user_role(org_id, user_email, payload.role)
    if error == "user_not_found":
        return 404, {"message": f"User '{user_email}' not found in this organization"}

    return 200, org_user


@router.delete(
    "/{org_id}/users/{user_email}",
    response={204: None, 403: ErrorMessage, 404: ErrorMessage},
)
@require_org_roles(ORG_MANAGEMENT_ROLES)
async def remove_org_user(request, org_id: UUID, user_email: str):
    success, error = await remove_organization_user(org_id, user_email)
    if error == "user_not_found":
        return 404, {"message": f"User '{user_email}' not found in this organization"}
    if error == "cannot_remove_admin_or_owner":
        return 403, {"message": "Cannot remove an owner or admin from the organization"}

    return 204, None
