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

import logging

from ninja import Router
from typing import List
from uuid import UUID
from django.http import HttpResponse

from organization.schemas import (
    DeviceIn,
    DeviceUpdate,
    DeviceOut,
    DeviceDetailOut,
    DeviceConfigurationIn,
    DeviceConfigurationOut,
    DeviceConnectionStatusOut,
    DeviceInstallationDetailsOut,
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
    generate_device_access_token,
    get_organization,
    ResourceService
)
from authentication.constants import (
    ORG_ADMIN_ROLES,
    OrganizationRoleType,
)
from authentication.services import AuthBearer
from organization.decorators import require_org_roles

router = Router(tags=["Devices"], auth=AuthBearer())

logger = logging.getLogger(__name__)


def _get_jwt_token(request) -> str:
    """Extract the raw JWT token from the Authorization header."""
    auth_header:str|None = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header:
        return ""
    return auth_header.removeprefix("Bearer ").removeprefix("bearer").strip()


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
        os_type=payload.os_type.value if payload.os_type else None,
        os_version=payload.os_version.value if payload.os_version else None,
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
        os_type=device.os_type,
        os_version=device.os_version,
        script_downloaded_at=device.script_downloaded_at,
        script_downloaded_by=device.script_downloaded_by,
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
        os_type=payload.os_type.value if payload.os_type else None,
        os_version=payload.os_version.value if payload.os_version else None,
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
        os_type=device.os_type,
        os_version=device.os_version,
        script_downloaded_at=device.script_downloaded_at,
        script_downloaded_by=device.script_downloaded_by,
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
            os_type=device.os_type,
            os_version=device.os_version,
            script_downloaded_at=device.script_downloaded_at,
            script_downloaded_by=device.script_downloaded_by,
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
        os_type=device.os_type,
        os_version=device.os_version,
        script_downloaded_at=device.script_downloaded_at,
        script_downloaded_by=device.script_downloaded_by,
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
        os_type=device.os_type,
        os_version=device.os_version,
        script_downloaded_at=device.script_downloaded_at,
        script_downloaded_by=device.script_downloaded_by,
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
    "/{org_id}/{device_id}/installation-details",
    response={400: ErrorMessage, 403: ErrorMessage, 404: ErrorMessage, 200:DeviceInstallationDetailsOut, 402: DeviceInstallationDetailsOut},
)
@require_org_roles(list(OrganizationRoleType))
async def fetch_installation_details(request, org_id: UUID, device_id: UUID):
    device = await get_device_details(org_id, device_id)
    if not device:
        return 404, {"message": "Device not found"}
    
    user_token = _get_jwt_token(request)
    if not user_token or len(user_token) == 0:
        return 403, {"message": "Authorization token is missing or invalid."}
    
    organization = await get_organization(org_id)
    if not organization:
        return 404, {"message": "Organization not found"}
    
    if not organization.last_paid_at:
        return 402, DeviceInstallationDetailsOut(
            api_key="N/A",
            organization_id=org_id,
            device_id=device.id,
            message="Your current subscription does not allow downloading the installation script. Please upgrade your subscription to access this feature. Contact zuhairmhtb@gmail.com for further details."
        )

    if not device.api_key:       
        logger.info("No API key found for device %s. Generating new access token.", device_id)        
        try:
            async with ResourceService(jwt_token=user_token) as resource_service:
                resource = await resource_service.get_organization(str(org_id))
                if not resource or not resource.indices or len(resource.indices) == 0:
                    return 404, {"message": "Organization resources not found. Please make sure you provisioned the resource"}
        except Exception as e:
            logger.error("Failed to retrieve organization resources for org %s: %s", org_id, e)
            return 400, {"message": "Failed to retrieve organization resources."}
        


        token, error = await generate_device_access_token(
            device_id=device.id,
            organization_id=org_id,
            resources=resource.indices
        )
        if error:
            logger.error("Failed to generate access token for device %s: %s", device_id, error)
            return 400, {"message": "Failed to generate access token for the device."}
    else:
        token = device.api_key

    return DeviceInstallationDetailsOut(
        api_key=token,
        organization_id=org_id,
        device_id=device.id
    )
