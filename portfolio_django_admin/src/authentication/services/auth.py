from ninja.security import HttpBearer
from jose import JWTError, jwt
from django.conf import settings
from datetime import datetime, timedelta
from typing import Optional, List
import json
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from authentication.models import UserRole
from authentication.constants import RoleType
from asgiref.sync import sync_to_async



class AuthBearer(HttpBearer):
    async def authenticate(self, request, token):
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            return None
        
@sync_to_async
def get_roles(user:AbstractUser)->list[RoleType]:
    roles = list(UserRole.objects.filter(user=user).values_list('role', flat=True))
    if not roles:
        roles = [RoleType.GUEST.value]
    return roles

async def get_access_token_payload(username:str, expires_delta: Optional[timedelta] = None)->dict:
    to_encode = {"sub": username}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    user = await get_user_model().objects.aget(username=username)
    
    # Get user roles from database
    roles = await get_roles(user)
    
    # If no roles assigned, default to GUEST
    if not roles:
        roles = [RoleType.GUEST.value]
    
    to_encode.update({
        "exp": expire,
        "roles": roles
    })
    return to_encode

async def create_access_token(username:str, expires_delta: Optional[timedelta] = None):
    encoded_jwt = jwt.encode(
        await get_access_token_payload(username, expires_delta),
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_token(token:str)->dict:
    return jwt.decode(
        token, 
        settings.JWT_SECRET_KEY, 
        algorithms=[settings.JWT_ALGORITHM]
    )

def get_refresh_token_payload(username:str, expires_delta: Optional[timedelta]=None)->dict:
    to_encode = {"sub": username}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "token_type": "refresh"
    })
    return to_encode

def create_refresh_token(username:str, expires_delta: Optional[timedelta] = None):
    encoded_jwt = jwt.encode(
        get_refresh_token_payload(username, expires_delta),
        settings.JWT_REFRESH_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def verify_refresh_token(refresh_token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_REFRESH_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("token_type") != "refresh":
            return None
        return payload
    except JWTError:
        return None


def create_device_access_token(
    device_id: str,
    organization_id: str,
    device_type: str,
    elastic_indices: List[dict],
    os_type: Optional[str]=None,
    os_version: Optional[str]=None,
) -> str:
    """
    Generate a non-expiring JWT access token for a device.

    The token payload contains:
    - sub: device ID
    - organization_id: the organization the device belongs to
    - device_type: the type of device
    - elastic_indices: JSON-encoded list of Elastic Indices configured for the device
    - os_type: (optional) operating system type
    - os_version: (optional) operating system versions
    """
    payload = {
        "sub": device_id,
        "organization_id": organization_id,
        "device_type": device_type,
        "resources": json.dumps(elastic_indices),
    }
    if os_type:
        payload["os_type"] = os_type
    if os_version:
        payload["os_version"] = os_version

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)