"""
Available Routes:

# Post, Put, Delete Methods (requires admin role of organization)
1. Add device
2. Deactivate device
3. Remove Device
4. Add Device Configuration
5. Remove Device Configuration
6. Download Installation File

# Get Methods
1. List Devices
2. Get Device Details
3. Check Connection Status
"""

from ninja import Router
from typing import List
from uuid import UUID
from organization.schemas import (
    DeviceIn,
    DeviceUpdate,
    DeviceOut,
    DeviceDetailOut,
    DeviceConfigurationIn,
    DeviceConfigurationOut,
    DeviceConnectionStatusOut,
    ErrorMessage,
)
from organization.services import (
    add_device,
    update_device,
    list_devices,
    get_device_details,
    deactivate_device,
    remove_device,
    add_device_configuration,
    remove_device_configuration,
    get_device_connection_status,
)
from authentication.constants import (
    ORG_ADMIN_ROLES,
    OrganizationRoleType,
)
from authentication.services import AuthBearer
from organization.decorators import require_org_roles

router = Router(tags=["Devices"], auth=AuthBearer())


# ---------------------------------------------------------------------------
# Device endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{org_id}/",
    response={201: DeviceOut, 400: ErrorMessage, 403: ErrorMessage, 409: ErrorMessage},
)
@require_org_roles(ORG_ADMIN_ROLES)
async def add_device_endpoint(request, org_id: UUID, payload: DeviceIn):
    device, error = await add_device(
        org_id=org_id,
        name=payload.name,
        device_type=payload.device_type.value,
        description=payload.description,
        updated_by=request.auth["sub"],
    )
    if error:
        return 409, {"message": error}

    return 201, DeviceOut(
        id=device.id,
        organization_id=org_id,
        name=device.name,
        description=device.description,
        device_type=device.device_type,
        is_active=device.is_active,
        created_at=device.created_at,
        updated_at=device.updated_at,
        last_heartbeat_at=device.last_heartbeat_at,
    )

@router.put(
    "/{org_id}/{device_id}/",
    response={200: DeviceOut, 400: ErrorMessage, 403: ErrorMessage, 404: ErrorMessage, 409: ErrorMessage},
)
@require_org_roles(ORG_ADMIN_ROLES)
async def update_device_endpoint(request, org_id: UUID, device_id: UUID, payload: DeviceUpdate):
    device, error = await update_device(
        org_id=org_id,
        device_id=device_id,
        name=payload.name,
        description=payload.description,
    )

    if error:
        return 404, {"message": error}
    return 200, DeviceOut(
        id=device.id,
        organization_id=org_id,
        name=device.name,
        description=device.description,
        device_type=device.device_type,
        is_active=device.is_active,
        created_at=device.created_at,
        updated_at=device.updated_at,
        last_heartbeat_at=device.last_heartbeat_at,
    )

@router.get(
    "/{org_id}/",
    response={200: List[DeviceOut], 403: ErrorMessage},
)
@require_org_roles(list(OrganizationRoleType))
async def list_devices_endpoint(request, org_id: UUID):
    devices = await list_devices(org_id)
    return 200, [
        DeviceOut(
            id=device.id,
            organization_id=org_id,
            name=device.name,
            description=device.description,
            device_type=device.device_type,
            is_active=device.is_active,
            created_at=device.created_at,
            updated_at=device.updated_at,
            last_heartbeat_at=device.last_heartbeat_at,
        )
        async for device in devices
    ]


@router.get(
    "/{org_id}/{device_id}",
    response={200: DeviceDetailOut, 403: ErrorMessage, 404: ErrorMessage},
)
@require_org_roles(list(OrganizationRoleType))
async def get_device_details_endpoint(request, org_id: UUID, device_id: UUID):
    device = await get_device_details(org_id, device_id)
    if not device:
        return 404, {"message": "Device not found"}

    configurations = [
        DeviceConfigurationOut(
            id=config.id,
            device_id=device.id,
            data_type=config.data_type,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
        for config in device.configurations.all() if hasattr(device, 'configurations')
    ]

    return 200, DeviceDetailOut(
        id=device.id,
        organization_id=org_id,
        name=device.name,
        description=device.description,
        device_type=device.device_type,
        is_active=device.is_active,
        created_at=device.created_at,
        updated_at=device.updated_at,
        last_heartbeat_at=device.last_heartbeat_at,
        configurations=configurations,
    )


@router.post(
    "/{org_id}/{device_id}/deactivate",
    response={200: DeviceOut, 400: ErrorMessage, 403: ErrorMessage, 404: ErrorMessage},
)
@require_org_roles(ORG_ADMIN_ROLES)
async def deactivate_device_endpoint(request, org_id: UUID, device_id: UUID):
    device, error = await deactivate_device(org_id, device_id, updated_by=request.auth["sub"])
    if error:
        return 404, {"message": error}

    return 200, DeviceOut(
        id=device.id,
        organization_id=org_id,
        name=device.name,
        description=device.description,
        device_type=device.device_type,
        is_active=device.is_active,
        created_at=device.created_at,
        updated_at=device.updated_at,
        last_heartbeat_at=device.last_heartbeat_at,
    )


@router.delete(
    "/{org_id}/{device_id}",
    response={204: None, 403: ErrorMessage, 404: ErrorMessage},
)
@require_org_roles(ORG_ADMIN_ROLES)
async def remove_device_endpoint(request, org_id: UUID, device_id: UUID):
    success, error = await remove_device(org_id, device_id)
    if error:
        return 404, {"message": error}

    return 204, None


# ---------------------------------------------------------------------------
# Device configuration endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{org_id}/{device_id}/configurations",
    response={201: DeviceConfigurationOut, 403: ErrorMessage, 404: ErrorMessage, 409: ErrorMessage},
)
@require_org_roles(ORG_ADMIN_ROLES)
async def add_device_configuration_endpoint(request, org_id: UUID, device_id: UUID, payload: DeviceConfigurationIn):
    config, error = await add_device_configuration(org_id, device_id, payload.data_type.value)
    if error:
        return 409 if "already exists" in error else 404, {"message": error}

    return 201, DeviceConfigurationOut(
        id=config.id,
        device_id=device_id,
        data_type=config.data_type,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.delete(
    "/{org_id}/{device_id}/configurations/{config_id}",
    response={204: None, 403: ErrorMessage, 404: ErrorMessage},
)
@require_org_roles(ORG_ADMIN_ROLES)
async def remove_device_configuration_endpoint(request, org_id: UUID, device_id: UUID, config_id: UUID):
    success, error = await remove_device_configuration(org_id, device_id, config_id)
    if error:
        return 404, {"message": error}

    return 204, None


# ---------------------------------------------------------------------------
# Device connection status endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/{org_id}/{device_id}/status",
    response={200: DeviceConnectionStatusOut, 403: ErrorMessage, 404: ErrorMessage},
)
@require_org_roles(list(OrganizationRoleType))
async def check_connection_status_endpoint(request, org_id: UUID, device_id: UUID):
    device = await get_device_connection_status(org_id, device_id)
    if not device:
        return 404, {"message": "Device not found"}

    return 200, DeviceConnectionStatusOut(
        device_id=device.id,
        is_active=device.is_active,
        last_heartbeat_at=device.last_heartbeat_at,
    )


# ---------------------------------------------------------------------------
# Download installation file endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/{org_id}/{device_id}/download",
    response={200: dict, 403: ErrorMessage, 404: ErrorMessage},
)
@require_org_roles(ORG_ADMIN_ROLES)
async def download_installation_file_endpoint(request, org_id: UUID, device_id: UUID):
    device = await get_device_connection_status(org_id, device_id)
    if not device:
        return 404, {"message": "Device not found"}

    return 200, {
        "message": "Installation file download is not yet available.",
        "device_id": str(device.id),
    }
