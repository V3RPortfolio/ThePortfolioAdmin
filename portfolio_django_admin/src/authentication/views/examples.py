from ninja import Router
from authentication.schemas import ErrorMessage
from authentication.decorators import require_roles
from authentication.constants import RoleType

router = Router(tags=["Examples"])


# @router.get("/me", response={200: dict, 401: ErrorMessage})
# async def me(request):
#     return {"username": request.auth["sub"]}

# Example protected endpoint
@router.get("/protected", response={200: dict, 401: ErrorMessage})
@require_roles([RoleType.ADMIN])
async def protected_route(request):
    return {"message": f"Hello {request.auth['sub']}! This is a protected endpoint"}

