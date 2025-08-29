from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name="index"),
    path('legislators/', views.legislators_view, name="legislators"),
    path('legislators/<int:legislator_id>/',
         views.legislator_detail_view, name='legislator_detail'),
    path('bills/', views.bills_view, name="bills"),
    path('bills/<int:bill_id>/', views.bill_detail_view, name='bill_detail'),
]
