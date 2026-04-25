from django.db import models
import uuid

from organization.constants import DeviceType, DeviceDataType, OsType, OsVersion
from .organization import Organization

# Create your models here.
class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True, null=True, max_length=500)
    device_type = models.CharField(
        max_length=20,
        choices=[(device_type.value, device_type.name) for device_type in DeviceType],
        default=DeviceType.DESKTOP.value
    )
    api_key = models.TextField(blank=True, null=True)
    os_type = models.CharField(
        max_length=50,
        choices=[(os.value, os.name) for os in OsType],
        default=OsType.UBUNTU.value
    )
    os_version = models.CharField(
        max_length=50, 
        choices=[(version.value, version.name) for version in OsVersion],
        default=OsVersion.UBUNTU_24.value
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    script_downloaded_at = models.DateTimeField(null=True, blank=True)
    script_downloaded_by = models.CharField(max_length=255, null=True, blank=True)

    configurations:list['DeviceConfiguration'] = []  # This will be populated manually in the service layer
    class Meta:
        unique_together = ('organization', 'name')
        db_table = 'devices'


class DeviceConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='configurations')
    data_type = models.CharField(
        max_length=50,
        choices=[(data_type.value, data_type.name) for data_type in DeviceDataType],
        blank=False,
        null=False
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('device', 'data_type')
        db_table = 'device_configurations'


