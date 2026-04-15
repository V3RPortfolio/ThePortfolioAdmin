from celery import shared_task
from organization.models import OrganizationUser


@shared_task
def process_invitation(invitation_id: str):
    try:
        invitation = OrganizationUser.objects.get(id=invitation_id)
        # Here you would add the logic to send an email invitation to the user
        # For example, you could use Django's send_mail function or any email service provider
        print(f"Processing invitation for {invitation.user.email} to join organization {invitation.organization.name}")
        # Simulate sending email
        # send_mail(subject, message, from_email, [invitation.user.email])
    except OrganizationUser.DoesNotExist:
        print(f"Invitation with id {invitation_id} does not exist.")