from django.urls import path
from .views import financial_reports_view

app_name = 'reports'
urlpatterns = [path('', financial_reports_view, name='financial_reports')]
