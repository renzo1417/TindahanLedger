from django.urls import path
from . import views

app_name = 'pos'
urlpatterns = [
    path('', views.terminal_view, name='pos_terminal'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('receipts/<int:sale_id>/', views.receipt_view, name='receipt'),
]
