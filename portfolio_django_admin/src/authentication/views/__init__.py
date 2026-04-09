from .authentication import router as auth_router
from .examples import router as examples_router
from .oauth2 import router as oauth2_router

__all__ = ["auth_router", "examples_router", "oauth2_router"]