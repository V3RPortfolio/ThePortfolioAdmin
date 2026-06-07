from typing import Optional
from datetime import datetime
from ninja import Schema
from uuid import UUID

class ServiceGroupOut(Schema):
    id: UUID
    title: str
    is_active: bool
    
class ServiceContentOut(Schema):
    id: UUID
    content: Optional[str] = None
    sequence_number: int

class ServiceOut(Schema):
    id: UUID
    title: str
    group: ServiceGroupOut
    contents: list[ServiceContentOut] = []

    created_at: datetime
    updated_at: Optional[datetime] = None
    
    
class ServiceInfoOut(Schema):
    id: UUID
    title: str
    
class ServiceGroupInfoOut(Schema):
    id: UUID
    title: str
    is_active: bool
    services: list[ServiceInfoOut] = []
