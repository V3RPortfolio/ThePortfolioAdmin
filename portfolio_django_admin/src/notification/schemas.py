from ninja import Schema
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class NotificationOut(Schema):
    id: UUID
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    is_read: bool
    notification_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class NotificationIn(Schema):
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    notification_type: Optional[str] = None

class PaginatedNotificationOut(Schema):
    items: List[NotificationOut]
    total: int
    page: int
    page_size: int


class ErrorMessage(Schema):
    message: str
