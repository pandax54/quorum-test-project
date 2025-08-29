from django.shortcuts import render
from django.http import HttpResponse
from .services import legislative_service


def index(request):
    stats = legislative_service.get_stats()

    context = {
        **stats,
    }
    return render(request, 'index.html', context)


def bills_view(request):
    bills_data = legislative_service.get_complete_bills_data()
    bills_table = legislative_service.render_table(bills_data)

    context = {
        'table': bills_table,
        'views': 'bills'
    }

    return render(request, 'table.html', context)


def legislators_view(request):
    legislators_data = legislative_service.get_complete_legislators_data()
    legislators_table = legislative_service.render_table(legislators_data)

    context = {
        'table': legislators_table,
        'views': 'legislators'
    }

    return render(request, 'table.html', context)
