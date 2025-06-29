from ninja.security import HttpBearer
from jose import JWTError, jwt
from django.conf import settings
from datetime import datetime, timedelta
from typing import Optional
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from authentication.models import UserRole, RoleType
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
        
class DeviceBearer(HttpBearer):
    async def authenticate(self, request, token):
        try:
            payload = jwt.decode(
                token, 
                settings.DEVICE_TOKEN_KEY, 
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

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    user = await get_user_model().objects.aget(username=data.get('sub'))
    
    # Get user roles from database
    roles = await get_roles(user)
    
    # If no roles assigned, default to GUEST
    if not roles:
        roles = [RoleType.GUEST.value]
    
    to_encode.update({
        "exp": expire,
        "roles": roles
    })
    encoded_jwt = jwt.encode(
        to_encode, 
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

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "token_type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
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

def create_device_token(device_data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT token for device authentication
    device_data should contain device identifiers like mac_address, device_id, etc.
    """
    to_encode = device_data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to 30 days for device tokens
        expire = datetime.utcnow() + timedelta(days=settings.DEVICE_TOKEN_EXPIRATION)
    
    to_encode.update({
        "exp": expire,
        "token_type": "device",
        "iat": datetime.utcnow()  # issued at time
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.DEVICE_TOKEN_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def verify_device_token(device_token: str) -> Optional[dict]:
    """
    Verify a device token and return its payload if valid
    """
    try:
        payload = jwt.decode(
            device_token,
            settings.DEVICE_TOKEN_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("token_type") != "device":
            return None
        return payload
    except JWTError:
        return None
