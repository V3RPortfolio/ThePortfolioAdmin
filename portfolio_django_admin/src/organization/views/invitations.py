from ninja import Router
from typing import List
from uuid import UUID
from organization.schemas import (
    OrganizationUserIn,
    OrganizationUserOut,
    OrganizationInvitationResponseIn,
    ErrorMessage,
)
from organization.services import (
    get_user_id_by_username,
    invite_organization_user,
    respond_to_organization_invite,
    get_invitation,
    list_pending_invitations
)
from authentication.constants import (
    ORG_ADMIN_ROLES,
    ORG_MANAGEMENT_ROLES,
    OWNER_ASSIGNABLE_ROLES,
    MANAGER_ASSIGNABLE_ROLES,
)
from authentication.services import AuthBearer
from organization.decorators import require_org_roles

router = Router(tags=["Organization"], auth=AuthBearer())

@router.post(
    "/{org_id}/respond",
    response={
        201: OrganizationUserOut,
        400: ErrorMessage,
        403: ErrorMessage,
        404: ErrorMessage,
        409: ErrorMessage,
    },
)
async def respond_to_org_invite(request, org_id: UUID, payload: OrganizationInvitationResponseIn):
    user_id = await get_user_id_by_username(request.auth["sub"])
    if not user_id:
        return 400, {"message": "User not found"}
    
    invitation = await get_invitation(user_id=user_id, org_id=org_id)
    if not invitation:
        return 404, {"message": "Invitation not found"}
    
    if invitation.invitation_status != "pending":
        return 400, {"message": f"Invitation has already been responded to with status '{invitation.invitation_status}'"}
    
    response, message = await respond_to_organization_invite(org_id=org_id, user_id=user_id, accept=payload.accept)
    if response is None:
        return 404, {"message": message or "Organization not found"}
    
    return 201, OrganizationUserOut(
        id=response.id,
        organization_id=org_id,
        email=response.user.email,
        role=response.role,
        created_at=response.created_at,
        updated_at=response.updated_at,
        invitation_status=response.invitation_status,
    )

@router.get(
    "/",
    response={200: List[OrganizationUserOut], 403: ErrorMessage},
)
async def list_org_invitations(request):
    user_id = await get_user_id_by_username(request.auth["sub"])
    if not user_id:
        return 400, {"message": "User not found"}
    
    invitations = await list_pending_invitations(user_id)
    return 200, [
        OrganizationUserOut(
            id=invite.id,
            organization_id=invite.organization.id,
            email=invite.user.email,
            role=invite.role,
            created_at=invite.created_at,
            updated_at=invite.updated_at,
            invitation_status=invite.invitation_status,
        )
        for invite in invitations
    ]

@router.post(
    "/{org_id}/invite",
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

    org_user, error = await invite_organization_user(
        org_id=org_id, email=payload.email, role=payload.role)
    if error == "user_not_found":
        return 404, {"message": f"User '{payload.email}' not found"}
    if error == "org_not_found":
        return 404, {"message": "Organization not found"}
    if error == "user_already_member":
        return 409, {"message": f"User '{payload.email}' is already a member of this organization"}

    return 201, OrganizationUserOut(
        id=org_user.id,
        organization_id=org_id,
        email=org_user.user.email,
        role=org_user.role,
        created_at=org_user.created_at,
        updated_at=org_user.updated_at,
        invitation_status=org_user.invitation_status,
    )

