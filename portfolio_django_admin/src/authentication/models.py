from enum import Enum
from django.db import models
from django.contrib.auth import get_user_model

class RoleType(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

User = get_user_model()

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.CharField(
        max_length=20,
        choices=[(role.value, role.name) for role in RoleType],
        default=RoleType.GUEST.value
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'role')
        db_table = 'user_roles'

    def __str__(self):
        return f"{self.user.username} - {self.role}"