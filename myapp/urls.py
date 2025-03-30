from django.urls import path
from . import views

urlpatterns = [
    path('', views.cedulas, name='cedulas'),  # Ruta principal para listar cédulas
    path('editar/<int:id>/', views.editar_cedula, name='editar_cedula'),  # Ruta para editar
    path('eliminar/<int:id>/', views.eliminar_cedula, name='eliminar_cedula'),  # Ruta para eliminar
]