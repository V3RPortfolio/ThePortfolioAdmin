from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from jarvis_services.models import ServiceGroup, Service

from jarvis_services.schemas import ServiceGroupInfoOut

from typing import Optional, List
from uuid import UUID

User = get_user_model()

@sync_to_async
def get_service(service_id: UUID) -> Optional[Service]:
    try:
        service = Service.objects.select_related("group").prefetch_related("contents").get(id=service_id)
        return service
    except Service.DoesNotExist:
        return None
    
@sync_to_async
def get_services_by_group(group_id: UUID) -> Optional[ServiceGroupInfoOut]:
    try:
        group = ServiceGroup.objects.get(id=group_id)
        group_schema = ServiceGroupInfoOut.from_orm(group)
        if not group.is_active:
            return None

        group_schema.services = sorted(group_schema.services, key=lambda s: s.sequence_number)        
        return group_schema
    except ServiceGroup.DoesNotExist:
        return None
    
@sync_to_async
def get_all_service_groups() -> List[ServiceGroupInfoOut]:
    groups = ServiceGroup.objects.filter(is_active=True).all()
    group_schemas:list[ServiceGroupInfoOut] = []
    for group in groups:
        group_schemas.append(ServiceGroupInfoOut.from_orm(group))
        group_schemas[-1].services = sorted(group_schemas[-1].services, key=lambda s: s.sequence_number)
    return group_schemas