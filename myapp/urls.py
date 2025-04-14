from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # Ruta para el login
    path('logout/', views.logout_view, name='logout'),  # Ruta para cerrar sesión
    path('cedulas/', views.cedulas, name='cedulas'),  # Ruta protegida para cedulas.html
    path('eliminar/<int:id>/', views.eliminar_cedula, name='eliminar_cedula'),
]