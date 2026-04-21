from ninja import Router
from organization.views import organization_router, invitations_router, devices_router, resources_router

router = Router()
router.add_router("/invitations", invitations_router)
router.add_router("/devices", devices_router)
router.add_router("", resources_router)
router.add_router("", organization_router)
