from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Esto debe estar definido en views.py
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cedulas/', views.cedulas, name='cedulas'),
    path('guardar/', views.guardar_cedula, name='guardar_cedula'),
    path('eliminar/<int:id>/', views.eliminar_cedula, name='eliminar_cedula'),
    
    # Calendario
    path('calendario/', views.calendario_view, name='calendario'),
    path('eventos-json/', views.eventos_json, name='eventos_json'),
    path('guardar-evento/', views.guardar_evento, name='guardar_evento'),
    path('modificar-evento/<int:evento_id>/', views.modificar_evento, name='modificar_evento'),
    path('eliminar-evento/<int:evento_id>/', views.eliminar_evento, name='eliminar_evento'),
]