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

class DeviceTokenPayload(Schema):
    device_id: str
    device_name: str
    device_mac: str

    @staticmethod
    def is_same_device(request: HttpRequest, device_id: int):
        if not request.device_info:
            return False
        return request.device_info.get("device_id") == device_id


