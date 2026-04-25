from ninja import Router
from uuid import UUID
from organization.schemas.resources import ManageResourceDto, ResourceDto
from organization.schemas import ErrorMessage
from organization.services import ResourceService
from authentication.constants import ORG_ADMIN_ROLES
from authentication.services import AuthBearer
from organization.decorators import require_org_roles

router = Router(tags=["Organization Resources"], auth=AuthBearer())

import logging
logger = logging.getLogger(__name__)


def _get_jwt_token(request) -> str:
    """Extract the raw JWT token from the Authorization header."""
    auth_header:str|None = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header:
        return ""
    return auth_header.removeprefix("Bearer ").removeprefix("bearer").strip()


# ---------------------------------------------------------------------------
# Resource endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{org_id}/resources",
    response={201: ResourceDto, 400: ErrorMessage, 403: ErrorMessage},
)
@require_org_roles(ORG_ADMIN_ROLES)
async def create_resource(request, org_id: UUID, payload: ManageResourceDto):
    """Creates a new organization resource."""
    token = _get_jwt_token(request)
    async with ResourceService(jwt_token=token) as svc:
        try:
            resource = await svc.create_organization(payload)
            return 201, resource
        except Exception as e:
            logger.error("Failed to create resource for org %s: %s", org_id, e)
            return 400, {"message": "Unable to create resource. Please try again later."}


@router.post(
    "/{org_id}/resources/provision",
    response={200: dict, 400: ErrorMessage, 403: ErrorMessage},
)
@require_org_roles(ORG_ADMIN_ROLES)
async def provision_resource(request, org_id: UUID):
    """Provisions organization resource."""
    token = _get_jwt_token(request)
    async with ResourceService(jwt_token=token) as svc:
        try:
            result = await svc.provision_organization_index(str(org_id))
            return 200, result
        except Exception as e:
            logger.error("Failed to provision resource for org %s: %s", org_id, e)
            return 400, {"message": "Unable to provision resource. Please try again later."}


@router.get(
    "/{org_id}/resources",
    response={200: ResourceDto, 403: ErrorMessage, 404: ErrorMessage},
)
@require_org_roles(ORG_ADMIN_ROLES)
async def get_resource_status(request, org_id: UUID):
    """Gets the organization resource."""
    token = _get_jwt_token(request)
    async with ResourceService(jwt_token=token) as svc:
        try:
            resource = await svc.get_organization(str(org_id))
            return 200, resource
        except Exception as e:
            logger.error("Failed to retrieve resource for org %s: %s", org_id, e)
            return 404, {"message": "Resource not found or could not be retrieved."}


@router.patch(
    "/{org_id}/resources",
    response={200: ResourceDto, 400: ErrorMessage, 403: ErrorMessage, 404: ErrorMessage},
)
@require_org_roles(ORG_ADMIN_ROLES)
async def update_resource(request, org_id: UUID, payload: ManageResourceDto):
    """Updates organization resource."""
    token = _get_jwt_token(request)
    async with ResourceService(jwt_token=token) as svc:
        try:
            resource = await svc.update_organization(payload)
            return 200, resource
        except Exception as e:
            logger.error("Failed to update resource for org %s: %s", org_id, e)
            return 400, {"message": "Unable to update resource. Please try again later."}


@router.delete(
    "/{org_id}/resources",
    response={204: None, 403: ErrorMessage, 404: ErrorMessage},
)
@require_org_roles(ORG_ADMIN_ROLES)
async def delete_resource(request, org_id: UUID):
    """Deletes organization resource."""
    token = _get_jwt_token(request)
    async with ResourceService(jwt_token=token) as svc:
        try:
            await svc.delete_organization(str(org_id))
            return 204, None
        except Exception as e:
            logger.error("Failed to delete resource for org %s: %s", org_id, e)
            return 404, {"message": "Resource not found or could not be deleted."}
