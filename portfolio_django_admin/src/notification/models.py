from django.db import models
from django.contrib.auth import get_user_model
from notification.constants import NotificationType
import uuid

# Create your models here.
class UserNotification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500, null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    link_url = models.URLField(max_length=500, null=True, blank=True)

    is_read = models.BooleanField(default=False)    
    notification_type = models.CharField(max_length=20, null=True, blank=True, choices=[(tag, tag.value) for tag in NotificationType])
