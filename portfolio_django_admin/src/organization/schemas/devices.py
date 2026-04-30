from ninja import Schema
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from organization.constants import DeviceType, DeviceDataType, OsType, OsVersion


class DeviceIn(Schema):
    name: str
    description: Optional[str] = None
    device_type: DeviceType = DeviceType.DESKTOP
    os_type: Optional[OsType] = None
    os_version: Optional[OsVersion] = None

class DeviceUpdate(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    os_type: Optional[OsType] = None
    os_version: Optional[OsVersion] = None


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
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    script_downloaded_at: Optional[datetime] = None
    script_downloaded_by: Optional[str] = None

    configurations: List[DeviceConfigurationOut] = []


class DeviceDetailOut(DeviceOut):
    configurations: List["DeviceConfigurationOut"] = []


class DeviceConfigurationIn(Schema):
    data_type: DeviceDataType


class DeviceConnectionStatusOut(Schema):
    device_id: UUID
    is_active: bool
    last_heartbeat_at: Optional[datetime] = None

class DeviceInstallationDetailsOut(Schema):
    api_key: str
    organization_id: UUID
    device_id: UUID
    message: Optional[str] = None