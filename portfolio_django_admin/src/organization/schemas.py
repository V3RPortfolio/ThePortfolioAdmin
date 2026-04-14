from ninja import Schema
from typing import Optional
from uuid import UUID
from datetime import datetime
from authentication.constants import OrganizationRoleType


class OrganizationIn(Schema):
    name: str
    description: Optional[str] = None


class OrganizationUpdateIn(Schema):
    description: Optional[str] = None


class OrganizationOut(Schema):
    id: UUID
    name: str
    description: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    status: str


class OrganizationDetailOut(OrganizationOut):
    last_due_amount: float
    last_payment_due_date: Optional[datetime] = None
    last_paid_amount: str
    last_paid_at: Optional[datetime] = None
    last_payment_method: Optional[str] = None


class OrganizationUserIn(Schema):
    email: str
    role: OrganizationRoleType = OrganizationRoleType.VIEWER


class OrganizationUserUpdateIn(Schema):
    role: OrganizationRoleType


class OrganizationUserOut(Schema):
    id: int
    organization_id: UUID
    email: str
    role: str
    created_at: datetime
    updated_at: datetime
    invitation_status: str

    @staticmethod
    def resolve_email(obj):
        return obj.user.email


class ErrorMessage(Schema):
    message: str
