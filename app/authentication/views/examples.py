from ninja import Router
from authentication.schemas import ErrorMessage
from authentication.decorators import require_roles, require_device_token
from authentication.models import RoleType

router = Router()


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
