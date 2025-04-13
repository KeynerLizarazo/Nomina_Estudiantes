from django.urls import path
from . import views

urlpatterns = [
    path('', views.cedulas, name='cedulas'),
    path('eliminar/<int:id>/', views.eliminar_cedula, name='eliminar_cedula'),
]