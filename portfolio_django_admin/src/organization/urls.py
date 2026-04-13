from ninja import Router
from organization.views import organization_router

router = Router()
router.add_router("", organization_router)
