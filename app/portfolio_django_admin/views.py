from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.views.decorators.cache import cache_page


@cache_page(60 * 15)
def index(request: HttpRequest)->HttpResponse:
    return HttpResponse("Rage against the dying of the light.")