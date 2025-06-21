from ninja import Router
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from authentication.schemas import TokenPayload, AuthResponse, ErrorMessage, RefreshTokenPayload
from authentication.services.auth import create_access_token, AuthBearer, create_refresh_token, verify_refresh_token
from datetime import timedelta
from django.conf import settings
from asgiref.sync import sync_to_async
from authentication.decorators import require_roles, require_device_token
from authentication.models import RoleType

router = Router()


authenticate_user= sync_to_async(authenticate)
@router.post("/token", response={200: AuthResponse, 401: ErrorMessage}, auth=None)
async def login(request, payload: TokenPayload):
    user = await authenticate_user(username=payload.username, password=payload.password)
    if not user:
        return 401, {"message": "Invalid credentials"}
    
    access_token = await create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = create_refresh_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return 200, {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

@router.post("/refresh", response={200: AuthResponse, 401: ErrorMessage}, auth=None)
async def refresh_token(request, payload: RefreshTokenPayload):
    refresh_payload = verify_refresh_token(payload.refresh_token)
    if not refresh_payload:
        return 401, {"message": "Invalid refresh token"}
    
    access_token = await create_access_token(
        data={"sub": refresh_payload["sub"]},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = create_refresh_token(
        data={"sub": refresh_payload["sub"]},
        expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return 200, {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

@router.get("/me", response={200: dict, 401: ErrorMessage})
async def me(request):
    return {"username": request.auth["sub"]}

# Example protected endpoint
@router.get("/protected", response={200: dict, 401: ErrorMessage})
@require_roles([RoleType.ADMIN])
async def protected_route(request):
    return {"message": f"Hello {request.auth['sub']}! This is a protected endpoint"}

@router.get("/protected-device", response={200: dict, 401: ErrorMessage})
@require_device_token()
async def protected_device_route(request):
    return {
        "message": "Device authenticated successfully",
        "device_info": request.device_info
    }

# Example using combined device and role authentication
@router.get("/protected-device-admin", response={200: dict, 401: ErrorMessage})
@require_roles([RoleType.ADMIN])
@require_device_token()
async def protected_device_admin_route(request):
    return {
        "message": "Device and admin role authenticated successfully",
        "device_info": request.device_info,
        "username": request.auth['sub']
    }
