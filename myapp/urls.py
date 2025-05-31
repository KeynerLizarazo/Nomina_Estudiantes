from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # Ruta para el login
    path('logout/', views.logout_view, name='logout'),  # Ruta para cerrar sesión
    path('cedulas/', views.cedulas, name='cedulas'),  # Ruta protegida para cedulas.html
    path('eliminar/<int:id>/', views.eliminar_cedula, name='eliminar_cedula'),  # Ruta para eliminar un registro
    path('guardar/', views.guardar_cedula, name='guardar_cedula'),  # Nueva ruta para guardar/actualizar registros
    path('calendario/', views.calendario_view, name='calendario'),
    path('agregar/', views.agregar_evento, name='agregar_evento'),
    path('json/', views.eventos_json, name='eventos_json'),
    path('calendario/guardar/', views.guardar_evento, name='guardar_evento'),
    path('calendario/modificar/<int:evento_id>/', views.modificar_evento, name='modificar_evento'),
    path('calendario/eliminar/<int:evento_id>/', views.eliminar_evento, name='eliminar_evento'),
]