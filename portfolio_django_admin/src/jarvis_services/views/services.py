import logging

from ninja import Router
from uuid import UUID
from django.http import HttpResponse

from jarvis_services.schemas import (
    ServiceGroupInfoOut,
    ServiceOut,
    ErrorMessage
)

from jarvis_services.services import (
    get_service,
    get_services_by_group,
    get_all_service_groups,
)

router = Router(tags=["Services"], auth=None)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Service endpoints
# ---------------------------------------------------------------------------

@router.get("/service/{service_id}/", response={404: ErrorMessage, 200: ServiceOut})
async def get_service_endpoint(request, service_id: UUID):
    service = await get_service(service_id)
    if not service:
        return 404, ErrorMessage(message="Service not found")
    service = ServiceOut.from_orm(service)
    if service.contents:
        service.contents = sorted(service.contents, key=lambda c: c.sequence_number, reverse=False)
    return service

@router.get("/group/{group_id}/", response={404: ErrorMessage, 200: ServiceGroupInfoOut})
async def get_services_by_group_endpoint(request, group_id: UUID):
    group_info = await get_services_by_group(group_id)
    if not group_info:
        return 404, ErrorMessage(message="Service group not found")
    return group_info

@router.get("/groups/", response={200: list[ServiceGroupInfoOut]})
async def get_all_service_groups_endpoint(request):
    groups = await get_all_service_groups()
    return groups