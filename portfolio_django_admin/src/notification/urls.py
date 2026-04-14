from ninja import Router
from notification.views import router as notification_router

router = Router()
router.add_router("", notification_router)
