from django.contrib import admin
from .models import Organization, OrganizationUser

admin.site.register(Organization)
admin.site.register(OrganizationUser)
