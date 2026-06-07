from ninja import Router
from jarvis_services.views import services_api

router = Router()
router.add_router("", services_api)

__all__ = [
    "services_router",
]