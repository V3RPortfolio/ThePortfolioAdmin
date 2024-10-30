from django.http.request import HttpRequest
from django.http.response import HttpResponse, JsonResponse
from django.views.decorators.cache import cache_page
from django.middleware.csrf import get_token



@cache_page(60 * 15)
def index(request: HttpRequest)->HttpResponse:
    return HttpResponse("Rage against the dying of the light.")

def csrf(request: HttpRequest)->HttpResponse:
    token = get_token(request)
    response = JsonResponse({"csrfToken": token})

    response["X-CSRFToken"] = token
    return response