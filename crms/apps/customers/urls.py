"""
URL routes for the Customers and Utang Ledger app.
"""

from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_list_view, name='customer_list'),
    path('register/', views.customer_create_view, name='customer_create'),
    path('entries/', views.entry_view, name='entry'),
    path('entry/', views.entry_form_view, name='entry_form'),
    path('<int:customer_id>/', views.customer_detail_view, name='customer_detail'),
]
