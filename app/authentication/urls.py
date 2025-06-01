from django.contrib import admin
from django.urls import path, include
from portfolio_django_admin.views import index, csrf

from authentication.views import router as auth_api
from ninja import Router

router = Router()
router.add_router("", auth_api)