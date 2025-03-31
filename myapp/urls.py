from django.urls import path
from . import views

urlpatterns = [
    path('', views.cedulas, name='cedulas'),  # Ruta principal para listar cédulas
    path('eliminar/<int:id>/', views.eliminar_cedula, name='eliminar_cedula'),  # Ruta para eliminar
]