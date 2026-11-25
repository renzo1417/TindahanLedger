from django.urls import path
from . import views

app_name = 'profile'

urlpatterns = [
    path('', views.profile_view, name='index'),
    path('password/', views.password_change_view, name='change_password'),
]
