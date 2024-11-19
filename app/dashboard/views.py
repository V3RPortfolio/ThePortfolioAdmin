from django.shortcuts import render
from django.http.request import HttpRequest
from django.http.response import HttpResponse

from typing import Type

# Create your views here.
def index(request:Type[HttpRequest]):
    return HttpResponse("Hello, world. You're at the dashboard index.")