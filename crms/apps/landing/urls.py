from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('welcome/', views.landing_view, name='welcome'),
]
