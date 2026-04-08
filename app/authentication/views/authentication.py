from ninja import Router
from django.contrib.auth import authenticate
from authentication.schemas import TokenPayload, AuthResponse, ErrorMessage, RefreshTokenPayload
from authentication.services import create_access_token, create_refresh_token, verify_refresh_token
from datetime import timedelta
from django.conf import settings
from asgiref.sync import sync_to_async

router = Router()


authenticate_user= sync_to_async(authenticate)
@router.post("/token", response={200: AuthResponse, 401: ErrorMessage}, auth=None)
async def login(request, payload: TokenPayload):
    user = await authenticate_user(username=payload.username, password=payload.password)
    if not user:
        return 401, {"message": "Invalid credentials"}
    
    access_token = await create_access_token(
        username=user.username,
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = create_refresh_token(
        username=user.username,
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
        username=refresh_payload["sub"],
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = create_refresh_token(
        username=refresh_payload["sub"],
        expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return 200, {
        "access_token": access_token,
        "refresh_token": refresh_token
    }