from django.contrib import admin
from .models import Organization, OrganizationUser, Device, DeviceConfiguration

admin.site.register(Organization)
admin.site.register(OrganizationUser)
admin.site.register(Device)
admin.site.register(DeviceConfiguration)
