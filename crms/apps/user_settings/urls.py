from django.urls import path
from . import views

app_name = 'user_settings'

urlpatterns = [
    path('', views.user_settings_view, name='index'),
    path('reset/', views.reset_view, name='reset'),
    path('export/customers.csv', views.export_csv_view, name='export_csv'),
    path('export/ledger.json', views.export_json_view, name='export_json'),
]
