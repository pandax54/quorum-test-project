from django.shortcuts import render
from django.http import HttpResponse
from .services import legislative_service


def index(request):
    legislators = legislative_service.legislators

    return HttpResponse(legislators.to_html())
