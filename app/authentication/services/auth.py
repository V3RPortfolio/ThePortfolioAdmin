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
