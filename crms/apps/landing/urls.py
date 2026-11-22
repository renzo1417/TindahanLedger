from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    path('preview/', views.dashboard_preview, name='dashboard_preview'),
    path('', views.landing_view, name='landing'),
    path('welcome/', views.landing_view, name='welcome'),
]
