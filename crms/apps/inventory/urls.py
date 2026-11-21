"""
URL routes for the Inventory app.
"""

from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_list_view, name='inventory_list'),
    path('register/', views.product_create_view, name='product_create'),
    path('expiry/', views.expiry_tracker_view, name='expiry_tracker'),
    path('batches/<int:batch_id>/dispose/', views.dispose_view, name='dispose'),
    path('batches/<int:batch_id>/expiry/', views.expiry_update_view, name='correct_expiry'),
    path('<int:product_id>/restock/', views.restock_view, name='restock'),
    path('<int:product_id>/', views.product_detail_view, name='product_detail'),
]
