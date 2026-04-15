from notification.models import UserNotification
from notification.dto import PublishUserNotificationDTO
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import QuerySet
from typing import List, Tuple


async def create_notification(dto: PublishUserNotificationDTO) -> UserNotification:
    return await UserNotification.objects.acreate(
        user_id=dto.user_id,
        title=dto.title,
        description=dto.description,
        image_url=dto.image_url,
        link_url=dto.link_url,
        notification_type=dto.notification_type,
    )


async def get_user_id_by_username(username: str) -> int:
    try:
        return await get_user_model().objects.filter(username=username).values_list('id', flat=True).aget()
    except get_user_model().DoesNotExist:
        return None


async def get_user_notifications(user_id: int) -> QuerySet[UserNotification]:
    queryset = UserNotification.objects.filter(user_id=user_id).order_by('is_read', '-created_at')
    return queryset



async def get_user_unread_notifications(user_id: int) -> QuerySet[UserNotification]:
    queryset = UserNotification.objects.filter(user_id=user_id, is_read=False).order_by('-created_at')
    return queryset

async def mark_notifications_as_read(user_id: int, notification_ids: List[str]) -> int:
    notifications = await UserNotification.objects.filter(user_id=user_id, id__in=notification_ids).aupdate(is_read=True)
    if notifications == 0:
        raise ValueError("No notifications were marked as read. Please check the notification IDs and try again.")
    return notifications
