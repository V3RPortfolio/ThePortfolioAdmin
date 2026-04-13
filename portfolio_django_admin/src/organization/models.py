from enum import Enum
from django.db import models
from django.conf import settings
import uuid


class OrganizationRoleType(str, Enum):
    ADMIN = "admin"
    OWNER = "owner"
    MANAGER = "manager"
    EDITOR = "editor"
    VIEWER = "viewer"


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organizations'

    def __str__(self):
        return self.name


class OrganizationUser(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='organization_users'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organization_users'
    )
    role = models.CharField(
        max_length=20,
        choices=[(role.value, role.name) for role in OrganizationRoleType],
        default=OrganizationRoleType.VIEWER.value
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('organization', 'user')
        db_table = 'organization_users'

    def __str__(self):
        return f"{self.organization.name} - {self.user.username} - {self.role}"
