from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from organization.models.devices import Device
from organization.models.organization import OrganizationUser
from authentication.constants import OrganizationRoleType
from notification.tasks.process_notification import publish_notification

logger = logging.getLogger(__name__)

HEARTBEAT_TIMEOUT_HOURS = 24


@shared_task(ignore_result=True)
def manage_device_connections():
    """
    Periodically checks all devices for missed heartbeats.
    If a device's last_heartbeat_at is not null and the current time is more than
    24 hours past the last heartbeat, the task collects all such devices per
    organization and notifies users with ADMIN or MANAGER roles.
    """
    now = timezone.now()
    cutoff = now - timedelta(hours=HEARTBEAT_TIMEOUT_HOURS)

    # Fetch all devices whose last heartbeat has timed out
    timed_out_devices = Device.objects.filter(
        last_heartbeat_at__isnull=False,
        last_heartbeat_at__lt=cutoff,
        is_active=True,
    ).select_related('organization')

    if not timed_out_devices.exists():
        logger.info("manage_device_connections: No timed-out devices found.")
        return

    # Group timed-out devices by organization
    org_device_map: dict = {}
    for device in timed_out_devices:
        org_id = device.organization_id
        if org_id not in org_device_map:
            org_device_map[org_id] = {
                'organization': device.organization,
                'devices': [],
            }
        org_device_map[org_id]['devices'].append(device)

    admin_manager_roles = [
        OrganizationRoleType.ADMIN.value,
        OrganizationRoleType.MANAGER.value,
    ]

    for org_id, data in org_device_map.items():
        organization = data['organization']
        devices = data['devices']

        # Build a human-readable device list for the notification
        device_names = ', '.join(d.name for d in devices)
        device_count = len(devices)

        logger.info(
            f"manage_device_connections: Organization '{organization.name}' has "
            f"{device_count} device(s) with missed heartbeats: {device_names}"
        )

        # Find all ADMIN and MANAGER users in this organization
        org_users = OrganizationUser.objects.filter(
            organization_id=org_id,
            role__in=admin_manager_roles,
        ).select_related('user')

        if not org_users.exists():
            logger.warning(
                f"manage_device_connections: No ADMIN/MANAGER users found for "
                f"organization '{organization.name}' (id={org_id}). Skipping notifications."
            )
            continue

        title = f"[{organization.name}] Device Connection Alert"
        description = (
            f"{device_count} device(s) in your organization have not sent a heartbeat "
            f"in the last {HEARTBEAT_TIMEOUT_HOURS} hours: {device_names}. "
            f"Please check the device connectivity."
        )

        for org_user in org_users:
            user = org_user.user
            notification_data = {
                'user_id': user.id,
                'title': title,
                'description': description,
                'image_url': None,
                'link_url': None,
                'notification_type': 'warning',
            }
            try:
                publish_notification.delay(notification_data)
                logger.info(
                    f"manage_device_connections: Queued notification for user "
                    f"'{user.username}' (id={user.id}) in org '{organization.name}'."
                )
            except Exception as exc:
                logger.error(
                    f"manage_device_connections: Failed to queue notification for user "
                    f"'{user.username}' (id={user.id}): {exc}"
                )
