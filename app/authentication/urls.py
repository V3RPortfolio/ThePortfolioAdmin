from django.contrib import admin
from django.urls import path, include
from portfolio_django_admin.views import index, csrf

from authentication.views import api as auth_api

urlpatterns = [
    path('', auth_api.urls),
]