"""
URL configuration for portfolio_django_admin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from portfolio_django_admin.views import index, csrf
from authentication.urls import router as auth_api
from authentication.services.auth import AuthBearer, DeviceBearer
from vulnerability_analysis.urls import router as vulnerability_api
from django.conf import settings
from ninja import NinjaAPI, Redoc, Swagger  
from .constants import OPENAPI_DEVICE_EXTRA

api = NinjaAPI(
    auth=[AuthBearer()], 
    title="Portfolio API", 
    description="Portfolio API", 
    version="1.0.0", 
    docs=Swagger() if settings.DEBUG else Redoc(),
    urls_namespace="api",
    openapi_extra={
        "components": {
            "parameters": {
                data["name"]: data for data in OPENAPI_DEVICE_EXTRA["parameters"]
            }
        }
    }
)


api.add_router("/auth/v1/", auth_api)
api.add_router("/device/v1/", vulnerability_api)

urlpatterns = [
    path('', index, name='home'),
    path('admin/', admin.site.urls, name='admin'),
    path('csrf/', csrf, name='csrf'),
    path('github/', include('github.urls')),
    path('api/', api.urls),
]

if settings.DEBUG:
    # Add route for static files
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
