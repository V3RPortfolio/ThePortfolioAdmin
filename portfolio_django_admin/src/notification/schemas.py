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



class ErrorMessage(Schema):
    message: str

class NotificationReadStatusUpdateOut(Schema):
    is_read: bool
    total_updated: int

class NotificationReadStatusUpdatIn(Schema):
    notification_ids: List[str]