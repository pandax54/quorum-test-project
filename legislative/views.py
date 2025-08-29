from django.shortcuts import render
from django.http import HttpResponse
from .services import legislative_service


def index(request):
    return render(request, 'index.html')


def bills_view(request):
    bills = legislative_service.get_complete_bills_data()

    return HttpResponse(bills.to_html(
        justify='left'
    ))


def legislators_view(request):
    legislators = legislative_service.get_complete_legislators_data()

    return HttpResponse(legislators.to_html(
        justify='left'
    ))
