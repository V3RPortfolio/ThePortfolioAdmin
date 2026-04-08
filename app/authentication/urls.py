from django.contrib import admin
from django.urls import path, include
from portfolio_django_admin.views import index, csrf

from authentication.views import auth_router, examples_router, oauth2_router
from ninja import Router

router = Router()
router.add_router("", auth_router)
router.add_router("", examples_router)
router.add_router("oauth2/", oauth2_router)