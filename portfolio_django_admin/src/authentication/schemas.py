from ninja import Schema
from typing import Optional
from django.http import HttpRequest

class TokenPayload(Schema):
    username: str
    password: str

class AuthResponse(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenPayload(Schema):
    refresh_token: str

class ErrorMessage(Schema):
    message: str
class GoogleOAuth2RedirectUrlPayload(Schema):
    redirect_url: str
class GoogleOauth2Token(Schema):
    access_token: str
    id_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: Optional[str] = None
    scope: Optional[list[str]] = None
    expires_at: Optional[float] = None

class GoogleOauth2Info(Schema):
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    sub: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    email_verified: Optional[bool] = None

class DecodedToken(Schema):
    sub: str
    organization_id: Optional[str] = None
    resources: Optional[list[dict]] = None