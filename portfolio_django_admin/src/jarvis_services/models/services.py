from django.db import models
import uuid


class ServiceGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=False, null=False, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'service_groups'
        

class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=False, null=False)
    group = models.ForeignKey(ServiceGroup, on_delete=models.CASCADE, related_name='services')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)
    
    contents:list['ServiceContent'] = []

    class Meta:
        unique_together = ('title', 'group')
        db_table = 'services'
        
class ServiceContent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='contents')
    sequence_number = models.PositiveIntegerField(default=1)
    content = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'service_contents'