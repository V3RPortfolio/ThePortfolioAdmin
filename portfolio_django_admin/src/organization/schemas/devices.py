from ninja import Schema
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from organization.constants import DeviceType, DeviceDataType


class DeviceIn(Schema):
    name: str
    description: Optional[str] = None
    device_type: DeviceType = DeviceType.DESKTOP

class DeviceUpdate(Schema):
    name: Optional[str] = None
    description: Optional[str] = None


class DeviceConfigurationOut(Schema):
    id: UUID
    device_id: UUID
    data_type: str
    created_at: datetime
    updated_at: datetime
class DeviceOut(Schema):
    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str] = None
    device_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_heartbeat_at: Optional[datetime] = None

    configurations: List[DeviceConfigurationOut] = []


class DeviceDetailOut(DeviceOut):
    configurations: List["DeviceConfigurationOut"] = []


class DeviceConfigurationIn(Schema):
    data_type: DeviceDataType


class DeviceConnectionStatusOut(Schema):
    device_id: UUID
    is_active: bool
    last_heartbeat_at: Optional[datetime] = None