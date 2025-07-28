from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Esto debe estar definido en views.py
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('welcome/', views.welcome, name='welcome'),
    path('cedulas/', views.cedulas, name='cedulas'),
    path('cursos/', views.cursos, name='cursos'),
    path('niveles/', views.niveles, name='niveles'),
    path('guardar/', views.guardar_cedula, name='guardar_cedula'),
    path('eliminar/<int:id>/', views.eliminar_cedula, name='eliminar_cedula'),

    path('test-zone/', views.test_zone, name='test_zone'),

    # Calendario
    # path('calendario/', views.calendario_view, name='calendario'),
    # path('json/', views.eventos_json, name='eventos_json'),
    # path('guardar-evento/', views.guardar_evento, name='guardar_evento'),
    # path('modificar-evento/<int:evento_id>/', views.modificar_evento, name='modificar_evento'),
    # path('eliminar-evento/<int:evento_id>/', views.eliminar_evento, name='eliminar_evento'),
    # path('json/', views.eventos_json, name='eventos_json'),
    # path('calendario/guardar/', views.guardar_evento, name='guardar_evento'),
    # path('calendario/modificar/<int:evento_id>/', views.modificar_evento, name='modificar_evento'),
    # path('calendario/eliminar/<int:evento_id>/', views.eliminar_evento, name='eliminar_evento'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)