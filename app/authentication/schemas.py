from ninja import Schema
from typing import Optional

class TokenPayload(Schema):
    username: str
    password: str

class AuthResponse(Schema):
    access_token: str
    token_type: str = "bearer"

class ErrorMessage(Schema):
    message: str