from strawberry.django.views import AsyncGraphQLView
from django.http import HttpRequest, HttpResponse
from authentication.services.auth import decode_token

class CustomGraphQLView(AsyncGraphQLView):
    
    async def get_context(self, request:HttpRequest, response:HttpResponse):
        context = await super().get_context(request, response)
        return context
        