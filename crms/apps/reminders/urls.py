from django.urls import path
from . import views

app_name = 'reminders'
urlpatterns = [path('', views.reminders_view, name='sms_reminders'),
               path('<int:customer_id>/simulate/', views.simulate_view, name='simulate')]
