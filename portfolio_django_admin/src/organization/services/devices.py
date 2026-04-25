from django.db.models import QuerySet
from organization.models import Device, DeviceConfiguration

from typing import Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone
import json

from django.conf import settings
from jose import jwt as jose_jwt


async def add_device(
    org_id: UUID, name: str, device_type: str, description: Optional[str] = None, updated_by: Optional[str] = None
) -> Tuple[Optional[Device], Optional[str]]:
    if await Device.objects.filter(organization_id=org_id, name=name).aexists():
        return None, "A device with this name already exists in the organization."

    device = await Device.objects.acreate(
        organization_id=org_id,
        name=name,
        description=description,
        device_type=device_type,
        updated_by=updated_by,
    )
    return device, None


async def update_device(
    org_id: UUID, device_id: UUID, name: Optional[str] = None, description: Optional[str] = None,
):
    try:
        device = await Device.objects.aget(id=device_id, organization_id=org_id)
    except Device.DoesNotExist:
        return None, "Device not found in this organization."

    if name and name != device.name:
        if await Device.objects.filter(organization_id=org_id, name=name).aexists():
            return None, "A device with this name already exists in the organization."
        device.name = name

    if description is not None:
        device.description = description

    device.updated_at = datetime.now(timezone.utc)
    await device.asave()
    return device, None

async def list_devices(org_id: UUID) -> QuerySet[Device]:
    return Device.objects.filter(organization_id=org_id).order_by('name')


async def get_device_details(org_id: UUID, device_id: UUID) -> Optional[Device]:
    try:
        return await Device.objects.prefetch_related('configurations').aget(
            id=device_id, organization_id=org_id
        )
    except Device.DoesNotExist:
        return None


async def deactivate_device(
    org_id: UUID, device_id: UUID, updated_by: Optional[str] = None
) -> Tuple[Optional[Device], Optional[str]]:
    try:
        device = await Device.objects.aget(id=device_id, organization_id=org_id)
        if not device.is_active:
            return None, "The device is already deactivated."
        device.is_active = False
        device.updated_by = updated_by
        device.updated_at = datetime.now(timezone.utc)
        await device.asave()
        return device, None
    except Device.DoesNotExist:
        return None, "Device not found in this organization."


async def remove_device(org_id: UUID, device_id: UUID) -> Tuple[bool, Optional[str]]:
    try:
        device = await Device.objects.aget(id=device_id, organization_id=org_id)
        await device.adelete()
        return True, None
    except Device.DoesNotExist:
        return False, "Device not found in this organization."


async def add_device_configuration(
    org_id: UUID, device_id: UUID, data_type: str, configured_by: Optional[str] = None
) -> Tuple[Optional[DeviceConfiguration], Optional[str]]:
    try:
        device = await Device.objects.prefetch_related('configurations').aget(
            id=device_id, organization_id=org_id
        )
    except Device.DoesNotExist:
        return None, "Device not found in this organization."

    if await DeviceConfiguration.objects.filter(device=device, data_type=data_type).aexists():
        return None, "This configuration already exists for the device."

    existing_indices = [c.data_type for c in device.configurations.all()]
    all_indices = existing_indices + [data_type]

    # No 'exp' claim is set intentionally: this token serves as a long-lived
    # device API key whose lifecycle is managed via DeviceConfiguration records,
    # not token expiry.
    token_payload = {
        "device_id": str(device_id),
        "organization_id": str(org_id),
        "device_type": device.device_type,
        "elastic_indices": json.dumps(all_indices),
    }
    api_key = jose_jwt.encode(
        token_payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    config = await DeviceConfiguration.objects.acreate(
        device=device,
        data_type=data_type,
        organization_id=org_id,
        configured_by=configured_by,
        api_key=api_key,
    )
    return config, None


async def remove_device_configuration(
    org_id: UUID, device_id: UUID, config_id: UUID
) -> Tuple[bool, Optional[str]]:
    try:
        config = await DeviceConfiguration.objects.select_related('device').aget(
            id=config_id, device_id=device_id, device__organization_id=org_id
        )
        await config.adelete()
        return True, None
    except DeviceConfiguration.DoesNotExist:
        return False, "Configuration not found for this device."


async def get_device_connection_status(
    org_id: UUID, device_id: UUID
) -> Optional[Device]:
    try:
        return await Device.objects.only('id', 'is_active', 'last_heartbeat_at').aget(
            id=device_id, organization_id=org_id
        )
    except Device.DoesNotExist:
        return None
