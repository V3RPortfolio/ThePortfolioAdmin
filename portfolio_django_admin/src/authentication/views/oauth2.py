from uuid import uuid4
from ninja import Router
from django.http import HttpRequest
from django.conf import settings
from datetime import timedelta
from django.contrib.auth import get_user_model
from authentication.services import Oauth2Service, create_access_token, create_refresh_token
from authentication.schemas import GoogleOauth2Info, AuthResponse, GoogleOAuth2RedirectUrlPayload


import logging
logger = logging.getLogger(__name__)


router = Router()

@router.get("/login/google", auth=None, response={200: GoogleOAuth2RedirectUrlPayload})
async def google_oauth_login(request):
    oauth2_service = Oauth2Service(provider="google")
    redirect_url = await oauth2_service.get_redirect_url()
    return {"redirect_url": redirect_url}

@router.get("/callback/google", auth=None, response={200: AuthResponse, 500: dict})
async def google_oauth(request:HttpRequest):
    code = request.GET.get("code", "")
    scope = request.GET.get("scope", "")
    state = request.GET.get("state", "")
    error = request.GET.get("error", "")

    logger.info(f"Received Google OAuth callback with code: {code}, scope: {scope}, state: {state}, error: {error}")

    if error and len(error) > 0:
         return 500, {"message": f"Error during Google OAuth: {error}"}
   
    oauth2_service = Oauth2Service(provider="google")
    try:
        token = await oauth2_service.process_callback_code(state=state, code=code)

        if not token.access_token:
            raise ValueError("Failed to obtain access token from Google OAuth callback.")
        logger.info(f"Obtained access token from Google OAuth callback")
        
        user_info = await oauth2_service.get_user_info(token.access_token)
        if not user_info or not user_info.email:
            raise ValueError("Failed to obtain user info from Google OAuth callback.")
        
        logger.info(f"Obtained user info from Google OAuth callback: {user_info}")
        
        if not user_info.email:
            raise ValueError("User info does not contain email from Google OAuth callback.")
        try:
            user = await get_user_model().objects.aget(email=user_info.email)
        
            logger.info(f"User lookup by email '{user_info.email}' returned: {user}")
        except get_user_model().DoesNotExist:
            try:
                logger.info(f"User with email '{user_info.email}' does not exist. Attempting to create new user.")
                user = await get_user_model().objects.aget(username=user_info.email)
                if user:
                    logger.info(f"User with username '{user_info.email}' already exists. Generating unique username.")
                    username = user_info.email + "__" + str(uuid4())[:8]
                else:
                    logger.info(f"No user with username '{user_info.email}' found. Using email as username.")
                    username = user_info.email
            except get_user_model().DoesNotExist:
                logger.info(f"No user with username '{user_info.email}' found. Using email as username.")
                username = user_info.email

            user = await get_user_model().objects.acreate(
                email=user_info.email,
                username=username,
                first_name=user_info.given_name,
                last_name=user_info.family_name,
            )
            logger.info(f"Created new user with email '{user_info.email}' and username '{username}': {user}")
        access_token = await create_access_token(username=user.username, expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
        logger.info(f"Generated access token for user '{user.username}': {access_token}")
        refresh_token = create_refresh_token(username=user.username, expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS))
        logger.info(f"Generated refresh token for user '{user.username}': {refresh_token}")

        
        return 200, {"access_token": access_token, "refresh_token": refresh_token}
    except Exception as e:
        print(f"Error processing Google OAuth callback: {str(e)}")
        return 500, {"message": f"Error processing Google OAuth callback: {str(e)}"}
    
@router.get("/info", auth=None, response={200: GoogleOauth2Info, 400: dict, 404: dict, 500: dict})
async def get_user_info(request:HttpRequest, token:str|None=None):
    if not token:
        return 400, {"message": "Token is required"}
    
    try:
        oauth2_service = Oauth2Service(provider="google")
        user_info = await oauth2_service.get_user_info(token)
        if not user_info:
            return 404, {"message": "User info not found"}
        print("User info retrieved successfully:", user_info)
        return 200, user_info
    except Exception as e:
        print(f"Error initializing Oauth2Service: {str(e)}")
        return 500, {"message": f"Error initializing Oauth2Service: {str(e)}"}