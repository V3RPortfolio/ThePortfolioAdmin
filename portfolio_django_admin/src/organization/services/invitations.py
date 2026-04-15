from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from organization.models import Organization, OrganizationUser
from organization.constants import (
    OrganizationStatus,
    UserInvitationStatus
)
from organization.tasks import process_invitation
from notification.tasks import publish_notification
from notification.dto import PublishUserNotificationDTO
from notification.constants import NotificationType

from asgiref.sync import sync_to_async
from typing import Optional, List, Tuple
from uuid import UUID

User = get_user_model()


async def invite_organization_user(
    org_id: UUID, email: str, role: str, invited_by: str
) -> Tuple[Optional[OrganizationUser], Optional[str]]:
    try:
        user = await User.objects.aget(email=email)
    except User.DoesNotExist:
        return None, "The user with the provided email does not exist."

    try:
        org = await Organization.objects.exclude(status=OrganizationStatus.DELETED.value).aget(id=org_id)
    except Organization.DoesNotExist:
        return None, "The organization does not exist or has been deleted."

    if await OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).filter(organization=org, user=user).aexists():
        return None, "The user is already a member of the organization."

    org_user = await OrganizationUser.objects.acreate(organization=org, user=user, role=role, invited_by=invited_by)
    process_invitation.delay(str(org_user.id))
    publish_notification.delay(
        PublishUserNotificationDTO(
            user_id=user.id,
            description=f"You have been invited to join organization {org.name} as {role}.",
            title="Organization Invitation",
            notification_type=NotificationType.INVITATION.value
        ).model_dump()
    )
    return org_user, None



async def get_invitation(user_id: int, org_id: UUID) -> Optional[OrganizationUser]:
    try:
        return await OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).aget(
            organization_id=org_id, 
            user_id=user_id, 
            invitation_status=UserInvitationStatus.PENDING.value
        )
    except OrganizationUser.DoesNotExist:
        return None
    

async def list_pending_invitations(user_id: int) -> QuerySet[OrganizationUser]:
    return OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).filter(
            user_id=user_id, invitation_status=UserInvitationStatus.PENDING.value
        ).select_related('organization').select_related('user').order_by('created_at')


async def respond_to_organization_invite(
    org_id: UUID, user_id: int, accept: bool
) -> Tuple[Optional[OrganizationUser], Optional[str]]:
    try:
        org_user = await OrganizationUser.objects.exclude(organization__status=OrganizationStatus.DELETED.value).select_related('user', 'organization').aget(
            organization_id=org_id, user_id=user_id
        )
        if org_user.invitation_status != UserInvitationStatus.PENDING.value:
            return None, "The invitation has already been responded to."
        org_user.invitation_status = UserInvitationStatus.ACCEPTED.value if accept else UserInvitationStatus.DECLINED.value
        await org_user.asave()

        if accept:
            publish_notification.delay(
                PublishUserNotificationDTO(
                    user_id=user_id,
                    description=f"{org_user.user.email} has accepted the invitation to join organization {org_user.organization.name}.",
                    title="Organization Invitation Accepted",
                    notification_type=NotificationType.ALERT.value
                ).model_dump()
            )

            org_member_ids = OrganizationUser.objects.filter(organization_id=org_id).exclude(user_id=user_id).values_list('user_id', flat=True)
            async for member_id in org_member_ids:
                publish_notification.delay(
                    PublishUserNotificationDTO(
                        user_id=member_id,
                        description=f"{org_user.user.email} has joined the organization {org_user.organization.name} as {org_user.role}.",
                        title="New Organization Member",
                        notification_type=NotificationType.ALERT.value
                    ).model_dump()
                )

        else:
            invited_by = org_user.invited_by
            response = OrganizationUser()
            response.id = org_user.id
            response.organization = org_user.organization
            response.user = org_user.user
            response.role = org_user.role
            response.created_at = org_user.created_at
            response.invitation_status = org_user.invitation_status
            response.invited_by = org_user.invited_by

            await org_user.adelete()
            if invited_by:
                try:
                    user = await get_user_model().objects.aget(username=invited_by)
                except get_user_model().DoesNotExist:
                    user = None

                if user:
                    publish_notification.delay(
                        PublishUserNotificationDTO(
                            user_id=user.id,
                            description=f"{response.user.email} has declined the invitation to join organization {response.organization.name}.",
                            title="Organization Invitation Declined",
                            notification_type=NotificationType.ALERT.value
                        ).model_dump()
                    )
            return response, None

        return org_user, None
    except OrganizationUser.DoesNotExist:
        return None, "The invitation does not exist or has been deleted."