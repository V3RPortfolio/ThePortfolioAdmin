from ninja import Router
from notification.schemas import (
    NotificationIn,
    NotificationOut,
    ErrorMessage,
)
from authentication.services import AuthBearer
from notification.services import create_notification
from notification.models import UserNotification, NotificationType
from django.contrib.auth import get_user_model

router = Router(tags=["Notification"], auth=AuthBearer())


@router.post(
    "/create",
    response={201: NotificationOut, 400: ErrorMessage},
)
async def create_notifications(request, notification:NotificationIn):
    try:
        user = await get_user_model().objects.aget(username=request.auth["sub"])
    except get_user_model().DoesNotExist:
        return 400, {"message": "User not found"}

    user_notification = await create_notification(
        UserNotification(
            user_id=user.id,
            title=notification.title,
            description=notification.description,
            image_url=notification.image_url,
            link_url=notification.link_url,
            notification_type=notification.notification_type or NotificationType.ALERT,
        )
    )
    return 201, NotificationOut(
        id=user_notification.id,
        title=user_notification.title,
        description=user_notification.description,
        image_url=user_notification.image_url,
        link_url=user_notification.link_url,
        is_read=user_notification.is_read,
        notification_type=user_notification.notification_type,
        created_at=user_notification.created_at,
        updated_at=user_notification.updated_at,
    )