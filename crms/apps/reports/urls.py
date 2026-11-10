from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_view, name='index'),
    path('sales/', views.reports_view, name='sales'),
    path('aging/', views.reports_view, name='aging'),
]
