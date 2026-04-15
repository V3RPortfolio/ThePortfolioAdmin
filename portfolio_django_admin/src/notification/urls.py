from ninja import Router
from notification.views import notification_router, examples_router
from django.conf import settings

router = Router()
router.add_router("", notification_router)
if settings.DEBUG:
    router.add_router("", examples_router)
