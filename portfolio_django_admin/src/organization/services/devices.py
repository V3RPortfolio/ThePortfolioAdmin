import logging
import httpx

from django.db.models import QuerySet
from organization.models import Device, DeviceConfiguration
from organization.schemas import ResourceIndexDto
import portfolio_django_admin.constants as constants
from authentication.services.auth import create_device_access_token

from typing import Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def add_device(
    org_id: UUID,
    name: str,
    device_type: str,
    description: Optional[str] = None,
    updated_by: Optional[str] = None,
    os_type: Optional[str] = None,
    os_version: Optional[str] = None,
) -> Tuple[Optional[Device], Optional[str]]:
    if await Device.objects.filter(organization_id=org_id, name=name).aexists():
        return None, "A device with this name already exists in the organization."

    device = await Device.objects.acreate(
        organization_id=org_id,
        name=name,
        description=description,
        device_type=device_type,
        updated_by=updated_by,
        os_type=os_type,
        os_version=os_version,
    )

    return device, None


async def update_device(
    org_id: UUID,
    device_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    os_type: Optional[str] = None,
    os_version: Optional[str] = None,
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

    if os_type is not None:
        device.os_type = os_type

    if os_version is not None:
        device.os_version = os_version

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
    org_id: UUID, device_id: UUID, data_type: str
) -> Tuple[Optional[DeviceConfiguration], Optional[str]]:
    try:
        device = await Device.objects.aget(id=device_id, organization_id=org_id)
    except Device.DoesNotExist:
        return None, "Device not found in this organization."

    if await DeviceConfiguration.objects.filter(device=device, data_type=data_type).aexists():
        return None, "This configuration already exists for the device."

    config = await DeviceConfiguration.objects.acreate(
        device=device,
        data_type=data_type,
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

async def generate_device_access_token(
    device_id: UUID,
    organization_id: UUID,
    resources:list[ResourceIndexDto]
)->tuple[Optional[str], Optional[str]]:
    try:
        device = await Device.objects.aget(id=device_id, organization__id=organization_id)

        api_key = create_device_access_token(
            device_id=str(device.id),
            organization_id=str(organization_id),
            device_type=device.device_type,
            elastic_indices=[resource.model_dump() for resource in resources],
            os_type=device.os_type,
            os_version=device.os_version,
        )
        device.api_key = api_key
        await device.asave(update_fields=["api_key"])
        return api_key, None
    except Exception as e:
        logger.error("Failed to generate API key for device %s: %s", device.id, e)
        return None, "Failed to generate access token for the device."
    except Device.DoesNotExist:
        return None, "Device not found."

async def download_device_installation_script(
    org_id: UUID,
    device_name: str,
    jwt_token: str,
    downloaded_by: Optional[str] = None,
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Request the installation script binary for a device from the Organization Service.

    Sends a POST to /organization/{org_id}/installation with the device details and the
    device's JWT access token in the payload.  On success the binary content is returned
    and the device's script_downloaded_at / script_downloaded_by fields are updated.
    """
    try:
        device = await Device.objects.aget(organization_id=org_id, name=device_name)
    except Device.DoesNotExist:
        return None, "Device not found in this organization."

    try:
        async with httpx.AsyncClient(base_url=constants.ORGANIZATION_SERVICE_URL) as client:
            response = await client.get(
                f"/organization/{org_id}/download/v1?operating_system={device.os_type}&os_version={device.os_version}&software_version=latest",
                headers={"Authorization": f"Bearer {jwt_token}"},
            )
            response.raise_for_status()
            file_content = response.content
    except httpx.HTTPStatusError as e:
        logger.error(
            "Organization service returned an error for device installation script (org=%s, device=%s): %s",
            org_id, device_name, e,
        )
        return None, "Failed to retrieve installation script from the organization service."
    except Exception as e:
        logger.error(
            "Unexpected error while downloading installation script (org=%s, device=%s): %s",
            org_id, device_name, e,
        )
        return None, "An unexpected error occurred while downloading the installation script."

    # file_content = b"#!/bin/bash\necho 'This is a placeholder installation script.'\n"

    # try:
    #     device.script_downloaded_at = datetime.now(timezone.utc)
    #     device.script_downloaded_by = downloaded_by
    #     await device.asave(update_fields=["script_downloaded_at", "script_downloaded_by"])
    # except Exception as e:
    #     logger.error(
    #         "Failed to update script download metadata for device %s: %s", device.id, e
    #     )

    return file_content, None
