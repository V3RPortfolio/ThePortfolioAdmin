from ninja import Router
from notification.schemas import (
    PaginatedNotificationOut,
    ErrorMessage,
)
from notification.services import (
    get_user_notifications,
    get_user_unread_notifications,
)
from organization.services import get_user_id_by_username
from authentication.services import AuthBearer

router = Router(tags=["Notification"], auth=AuthBearer())


@router.get(
    "/",
    response={200: PaginatedNotificationOut, 400: ErrorMessage},
)
async def list_notifications(request, page: int = 1, page_size: int = 10):
    user_id = await get_user_id_by_username(request.auth["sub"])
    if not user_id:
        return 400, {"message": "User not found"}

    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    items, total = await get_user_notifications(user_id, page, page_size)
    return 200, {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/unread",
    response={200: PaginatedNotificationOut, 400: ErrorMessage},
)
async def list_unread_notifications(request, page: int = 1, page_size: int = 10):
    user_id = await get_user_id_by_username(request.auth["sub"])
    if not user_id:
        return 400, {"message": "User not found"}

    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    items, total = await get_user_unread_notifications(user_id, page, page_size)
    return 200, {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
