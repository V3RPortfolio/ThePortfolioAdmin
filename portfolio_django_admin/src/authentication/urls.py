from authentication.views import auth_router, examples_router, oauth2_router
from ninja import Router

router = Router()
router.add_router("", auth_router)
router.add_router("", examples_router)
router.add_router("oauth2/", oauth2_router)