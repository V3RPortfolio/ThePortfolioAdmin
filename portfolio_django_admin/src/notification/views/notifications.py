from ninja import Router
from ninja.pagination import paginate
from notification.schemas import (
    NotificationOut,
    ErrorMessage,
    NotificationReadStatusUpdatIn,
    NotificationReadStatusUpdateOut
)
from notification.services import (
    get_user_id_by_username,
    get_user_notifications,
    get_user_unread_notifications,
    mark_notifications_as_read
)
from authentication.services import AuthBearer

router = Router(tags=["Notification"], auth=AuthBearer())


@router.get(
    "/",
    response={200: list[NotificationOut], 400: ErrorMessage},
)
@paginate
async def list_notifications(request):
    user_id = await get_user_id_by_username(request.auth["sub"])
    if not user_id:
        return 400, {"message": "User not found"}

    items = await get_user_notifications(user_id)
    return [
        NotificationOut(
            id=item.id,
            title=item.title,
            description=item.description,
            image_url=item.image_url,
            link_url=item.link_url,
            is_read=item.is_read,
            notification_type=item.notification_type,
            created_at=item.created_at,
            updated_at=item.updated_at,
        ) async for item in items
    ]


@router.get(
    "/unread",
    response={200: list[NotificationOut], 400: ErrorMessage},
)
@paginate
async def list_unread_notifications(request):
    user_id = await get_user_id_by_username(request.auth["sub"])
    if not user_id:
        return 400, {"message": "User not found"}
    items = await get_user_unread_notifications(user_id)
    return [
        NotificationOut(
            id=item.id,
            title=item.title,
            description=item.description,
            image_url=item.image_url,
            link_url=item.link_url,
            is_read=item.is_read,
            notification_type=item.notification_type,
            created_at=item.created_at,
            updated_at=item.updated_at,
        ) async for item in items
    ]

@router.post(
    "/mark-read",
    response={200: NotificationReadStatusUpdateOut, 400: ErrorMessage},
)
async def mark_as_read(request, payload: NotificationReadStatusUpdatIn):
    user_id = await get_user_id_by_username(request.auth["sub"])
    if not user_id:
        return 400, {"message": "User not found"}

    total = await mark_notifications_as_read(user_id, payload.notification_ids)

    return 200, NotificationReadStatusUpdateOut(is_read=True, total_updated=total)