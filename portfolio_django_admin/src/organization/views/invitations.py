from ninja import Router
from typing import List
from uuid import UUID
from organization.schemas import (
    OrganizationUserIn,
    OrganizationInvitationResponseIn,
    OrganizationInvitationOut,
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
        201: OrganizationInvitationOut,
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
    
    return 201, OrganizationInvitationOut(
        id=response.id,
        organization_id=org_id,
        organization_name=response.organization.name,
        invited_email=response.user.email,
        invited_by=response.invited_by,
        role=response.role,
        created_at=response.created_at,
        invitation_status=response.invitation_status,
    )

@router.get(
    "/pending",
    response={200: List[OrganizationInvitationOut], 403: ErrorMessage},
)
async def list_org_invitations(request):
    user_id = await get_user_id_by_username(request.auth["sub"])
    if not user_id:
        return 400, {"message": "User not found"}
    
    invitations = await list_pending_invitations(user_id)
    return 200, [
        OrganizationInvitationOut(
            id=invite.id,
            organization_id=invite.organization.id,
            organization_name=invite.organization.name,
            invited_by=invite.invited_by,
            invited_email=invite.user.email,
            role=invite.role,
            created_at=invite.created_at,
            invitation_status=invite.invitation_status,
        )
        async for invite in invitations
    ]

@router.post(
    "/{org_id}/invite",
    response={
        201: OrganizationInvitationOut,
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
        org_id=org_id, 
        email=payload.email, 
        role=payload.role,
        invited_by=request.auth["sub"]
    )
    if error:
        return 404, {"message": error}

    return 201, OrganizationInvitationOut(
        id=org_user.id,
        organization_id=org_id,
        organization_name=org_user.organization.name,
        invited_by=org_user.invited_by,
        invited_email=org_user.user.email,
        role=org_user.role,
        created_at=org_user.created_at,
        invitation_status=org_user.invitation_status,
    )

