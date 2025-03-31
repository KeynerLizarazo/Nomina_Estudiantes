"""
URL configuration for nomina project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Ruta para el panel de administración
    path('admin/', admin.site.urls),

    # Incluir las URLs de la aplicación 'myapp'
    path('', include('myapp.urls')),  # Todas las rutas de 'myapp' estarán bajo la raíz ('/')
]