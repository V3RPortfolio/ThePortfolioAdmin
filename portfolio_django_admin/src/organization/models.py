from django.db import models
from django.contrib.auth import get_user_model
import uuid
from organization.constants import OrganizationStatus, PaymentCurrency, PaymentMethod, UserInvitationStatus
from authentication.constants import OrganizationRoleType


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.EmailField(max_length=255, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in OrganizationStatus],
        default=OrganizationStatus.ACTIVE.value,
        db_index=True
    )
    
    last_due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_payment_due_date = models.DateTimeField(null=True, blank=True)
    last_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_paid_currency = models.CharField(max_length=10, 
                                          choices=[(currency.value, currency.name) for currency in PaymentCurrency],
                                          null=True, blank=True)
    last_paid_at = models.DateTimeField(null=True, blank=True)
    last_payment_method = models.CharField(max_length=20, 
                                        choices=[(method.value, method.name) for method in PaymentMethod],
                                        null=True, blank=True)

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
        get_user_model(),
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

    invited_by = models.EmailField(max_length=255, null=True, blank=True)
    invitation_status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in UserInvitationStatus],
        default=UserInvitationStatus.PENDING.value,
        db_index=True
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    invitation_token = models.UUIDField(default=uuid.uuid4, null=True, blank=True)
    invitation_token_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('organization', 'user')
        db_table = 'organization_users'

    def __str__(self):
        return f"{self.organization.name} - {self.user.username} - {self.role}"
