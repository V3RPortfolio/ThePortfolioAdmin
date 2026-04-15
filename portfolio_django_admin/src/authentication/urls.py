from authentication.views import auth_router, examples_router, oauth2_router
from ninja import Router
from django.conf import settings

router = Router()
router.add_router("", auth_router)
if settings.DEBUG:
    router.add_router("", examples_router)
router.add_router("oauth2/", oauth2_router)