from django.shortcuts import render
from django.http import Http404
from .services import legislative_service


def index(request):
    stats = legislative_service.get_stats()

    context = {
        **stats,
    }
    return render(request, "index.html", context)


def bills_view(request):
    bills_data = legislative_service.get_complete_bills_data()
    bills_table = legislative_service.render_table(
        bills_data,
        [
            {
                "column_name": "sponsor",
                "url_pattern": "legislators",
                "name": "sponsor",
                "item_id": "sponsor_id",
                "css_class": "legislator-link",
                "should_link": lambda row: row["sponsor"] != "Unknown Sponsor",
            },
            {
                "column_name": "title",
                "url_pattern": "bills",
                "name": "title",
                "item_id": "id",
                "css_class": "bill-link",
            },
        ],
    )

    context = {"table": bills_table, "views": "bills"}

    return render(request, "table.html", context)


def legislators_view(request):
    legislators_data = legislative_service.get_complete_legislators_data()
    legislators_table = legislative_service.render_table(
        legislators_data,
        [
            {
                "column_name": "legislator",
                "url_pattern": "legislators",
                "name": "legislator",
                "item_id": "id",
                "css_class": "legislator-link",
            }
        ],
    )

    context = {"table": legislators_table, "views": "legislators"}

    return render(request, "table.html", context)


def bill_detail_view(request, bill_id):
    bill = legislative_service.get_bill_by_id(int(bill_id))

    if not bill:
        raise Http404("Bill not found")

    sponsor_link = (
        f'<a href="/legislators/{bill["sponsor_id"]}/" class="legislator-link">{bill["sponsor_name"]}</a>'
        if bill["sponsor_name"] != "Unknown Sponsor"
        else bill["sponsor_name"]
    )

    context = {"bill": bill, "sponsor_link": sponsor_link, "view": "bills"}

    return render(request, "bill_detail.html", context)


def legislator_detail_view(request, legislator_id):
    legislator = legislative_service.get_legislator_by_id(int(legislator_id))

    if not legislator:
        raise Http404("Legislator not found")

    context = {"legislator": legislator, "view": "legislators"}

    return render(request, "legislator_detail.html", context)
