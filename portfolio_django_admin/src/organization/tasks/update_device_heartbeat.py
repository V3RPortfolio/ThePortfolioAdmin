from celery import shared_task
from django.utils import timezone

from organization.models import Device


@shared_task
def update_device_heartbeat(organization_id: str, device_name: str):
    try:
        device = Device.objects.get(
            organization_id=organization_id,
            name=device_name
        )
        device.last_heartbeat_at = timezone.now()
        device.save(update_fields=["last_heartbeat_at"])
        print(
            f"Heartbeat updated for device '{device_name}' "
            f"in organization '{organization_id}' at {device.last_heartbeat_at}."
        )
    except Device.DoesNotExist:
        print(
            f"Device '{device_name}' not found in organization '{organization_id}'."
        )
