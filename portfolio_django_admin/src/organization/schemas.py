from ninja import Schema
from typing import List, Optional
from typing import Literal
from uuid import UUID
from datetime import datetime


OrganizationRoleLiteral = Literal["admin", "owner", "manager", "editor", "viewer"]


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
    username: str
    role: OrganizationRoleLiteral = "viewer"


class OrganizationUserUpdateIn(Schema):
    role: OrganizationRoleLiteral


class OrganizationUserOut(Schema):
    id: int
    organization_id: UUID
    username: str
    role: str
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_username(obj):
        return obj.user.username


class ErrorMessage(Schema):
    message: str
