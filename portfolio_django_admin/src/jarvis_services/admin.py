from django.contrib import admin
from .models import Service, ServiceGroup, ServiceContent

# Register your models here.
admin.site.register(ServiceGroup)
admin.site.register(Service)
admin.site.register(ServiceContent)
