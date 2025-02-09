from ninja import NinjaAPI
from django.contrib.auth import authenticate
from authentication.schemas import TokenPayload, AuthResponse, ErrorMessage
from authentication.services.auth import create_access_token, AuthBearer
from datetime import timedelta
from django.conf import settings
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AbstractUser

api = NinjaAPI(auth=AuthBearer())

@sync_to_async
def authenticate_user(username:str, password:str)->AbstractUser:
    return authenticate(username=username, password=password)

@api.post("/token", response={200: AuthResponse, 401: ErrorMessage}, auth=None)
async def login(request, payload: TokenPayload):
    user = await authenticate_user(username=payload.username, password=payload.password)
    if not user:
        return 401, {"message": "Invalid credentials"}
    
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return 200, {"access_token": access_token}

@api.get("/me", response={200: dict, 401: ErrorMessage})
async def me(request):
    return {"username": request.auth["sub"]}

# Example protected endpoint
@api.get("/protected", response={200: dict, 401: ErrorMessage})
async def protected_route(request):
    return {"message": f"Hello {request.auth['sub']}! This is a protected endpoint"}