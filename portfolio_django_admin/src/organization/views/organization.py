from ninja import Router
from typing import List
from uuid import UUID
from organization.schemas import (
    OrganizationIn,
    OrganizationUpdateIn,
    OrganizationOut,
    OrganizationUserUpdateIn,
    OrganizationUserOut,
    OrganizationLeaveOut,
    ErrorMessage,
)
from organization.services import (
    get_user_id_by_username,
    create_organization,
    get_user_organizations,
    get_organization,
    update_organization,
    delete_organization,
    list_organization_users,
    update_organization_user_role,
    remove_organization_user,
    select_organization,
    leave_organization
)
from authentication.constants import (
    OrganizationRoleType,
    ORG_ADMIN_ROLES,
    ORG_MANAGEMENT_ROLES,
    OWNER_ASSIGNABLE_ROLES,
    MANAGER_ASSIGNABLE_ROLES,
)
from authentication.services import AuthBearer
from organization.decorators import require_org_roles

router = Router(tags=["Organization"], auth=AuthBearer())


# ---------------------------------------------------------------------------
# Organization endpoints
# ---------------------------------------------------------------------------

@router.post("/", response={201: OrganizationOut, 400: ErrorMessage, 409: ErrorMessage})
async def create_org(request, payload: OrganizationIn):
    user_id = await get_user_id_by_username(request.auth["sub"])
    if not user_id:
        return 400, {"message": "User not found"}

    org, error = await create_organization(payload.name, user_id)
    if error == "name_taken":
        return 409, {"message": f"Organization with name '{payload.name}' already exists"}

    return 201, org


@router.get("/", response={200: List[OrganizationOut]})
async def list_orgs(request):
    user_id = await get_user_id_by_username(request.auth["sub"])
    if not user_id:
        return 200, []

    orgs = await get_user_organizations(user_id)
    return 200, orgs


@router.post("/{org_id}/select", response={200: dict, 400: ErrorMessage, 404: ErrorMessage})
async def select_org(request, org_id: UUID):
    user_id = await get_user_id_by_username(request.auth["sub"])
    if not user_id:
        return 400, {"message": "User not found"}

    role, error = await select_organization(user_id, org_id)
    if error == "user_not_in_organization":
        return 404, {"message": "User is not a member of this organization"}

    return 200, {"message": "Organization selected successfully", "role": role}


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
    org, error = await update_organization(org_id, payload.description, updated_by_username=request.auth["sub"])
    if error == "not_found":
        return 404, {"message": "Organization not found"}

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
    return 200, [
        OrganizationUserOut(
            id=user.id,
            organization_id=org_id,
            email=user.user.email,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
            invitation_status=user.invitation_status,
        )
        for user in users
    ]


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

    return 200, OrganizationUserOut(
        id=org_user.id,
        organization_id=org_id,
        email=org_user.user.email,
        role=org_user.role,
        created_at=org_user.created_at,
        updated_at=org_user.updated_at,
        invitation_status=org_user.invitation_status,
    )


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

@router.post(
    "/{org_id}/leave",
    response={
        201: OrganizationLeaveOut,
        400: ErrorMessage,
        403: ErrorMessage,
        404: ErrorMessage,
    },
)
@require_org_roles(list(OrganizationRoleType))
async def leave_org(request, org_id: UUID):
    user_id = await get_user_id_by_username(request.auth["sub"])
    if not user_id:
        return 400, {"message": "User not found"}

    success, error = await leave_organization(org_id=org_id, user_id=user_id)
    if error == "user_not_found":
        return 404, {"message": "User is not a member of this organization"}

    return 201, {"message": "You have left the organization successfully"}