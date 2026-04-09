from django.conf import settings
from requests_oauthlib import OAuth2Session
from authentication.schemas import GoogleOauth2Token, GoogleOauth2Info

class Oauth2Service:
    def __init__(self, provider:str):
        # Retrieve provider settings and use requests_oauthlib to handle oauth2 login
        self._oauth2_info:dict = settings.SOCIALACCOUNT_PROVIDERS or {}
        if not isinstance(self._oauth2_info, dict):
            raise ValueError("SOCIALACCOUNT_PROVIDERS must be a dictionary in settings")
        
        self._provider_info:dict = self._oauth2_info.get(provider)
        if not self._provider_info or not isinstance(self._provider_info, dict):
            raise ValueError(f"Provider '{provider}' not found in SOCIALACCOUNT_PROVIDERS settings")

        self._client_id = self._provider_info.get("client_id")
        self._client_secret = self._provider_info.get("client_secret")
        self._scope = self._provider_info.get("scope")
        self._authorization_url = self._provider_info.get("authorization_url")
        self._access_token_url = self._provider_info.get("access_token_url")
        self._userinfo_url = self._provider_info.get("userinfo_url")
        self._redirect_uri = self._provider_info.get("redirect_uri")

        if not self._client_id or \
            not self._client_secret or \
            not self._scope or \
            not self._authorization_url or \
            not self._access_token_url or \
            not self._userinfo_url or \
            not self._redirect_uri:
            raise ValueError(f"Provider '{provider}' is missing required OAuth2 configuration in settings.")  


    

    async def get_redirect_url(self)->str:
        """
        Returns the url of the provider along with client id, scopes, 
        and other required information.
        """
        provider = OAuth2Session(
            client_id=self._client_id, 
            scope=self._scope,
            redirect_uri=self._redirect_uri
        )
        _authorization_url = provider.authorization_url(self._authorization_url)
        return _authorization_url[0]
    
    async def process_callback_code(self, state:str|None, code:str|None)->GoogleOauth2Token:
        """
        Receives a code from the callback url and exchanges it for a access 
        token.

        @param state: The state returned by the provider
        @param code: The code returned by the provider
        returns Access token
        """
        provider = OAuth2Session(
            client_id=self._client_id, 
            state=state,
            redirect_uri=self._redirect_uri
        )
        token = provider.fetch_token(
            self._access_token_url,
            client_secret=self._client_secret,
            code=code
        )
        return GoogleOauth2Token.model_validate(token)
    
    async def get_user_info(self, access_token:str)->GoogleOauth2Info:
        """
        Receives an access token and uses it to retrieve user information from the provider.

        @param access_token: The access token obtained from the provider
        returns User information as a dictionary
        """
        provider = OAuth2Session(
            client_id=self._client_id, 
            token={"access_token": access_token},
            scope=self._scope,
            redirect_uri=self._redirect_uri
        )
        user_info = provider.get(self._userinfo_url).json()
        return GoogleOauth2Info.model_validate(user_info)