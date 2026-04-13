from ninja import Schema
from typing import Optional
from uuid import UUID
from datetime import datetime
from organization.constants import OrganizationRoleType


class OrganizationIn(Schema):
    name: str


class OrganizationUpdateIn(Schema):
    name: str


class OrganizationOut(Schema):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


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

    @staticmethod
    def resolve_email(obj):
        return obj.user.email


class ErrorMessage(Schema):
    message: str
