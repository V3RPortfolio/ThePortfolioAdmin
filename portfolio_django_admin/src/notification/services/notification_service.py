from notification.models import UserNotification
from notification.dto import PublishUserNotificationDTO
from asgiref.sync import sync_to_async
from typing import List, Tuple


def create_notification(dto: PublishUserNotificationDTO) -> UserNotification:
    return UserNotification.objects.create(
        user_id=dto.user_id,
        title=dto.title,
        description=dto.description,
        image_url=dto.image_url,
        link_url=dto.link_url,
        notification_type=dto.notification_type,
    )


@sync_to_async
def get_user_notifications(user_id: int, page: int = 1, page_size: int = 10) -> Tuple[List[UserNotification], int]:
    queryset = UserNotification.objects.filter(user_id=user_id).order_by('is_read', '-created_at')
    total = queryset.count()
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])
    return items, total


@sync_to_async
def get_user_unread_notifications(user_id: int, page: int = 1, page_size: int = 10) -> Tuple[List[UserNotification], int]:
    queryset = UserNotification.objects.filter(user_id=user_id, is_read=False).order_by('-created_at')
    total = queryset.count()
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])
    return items, total
