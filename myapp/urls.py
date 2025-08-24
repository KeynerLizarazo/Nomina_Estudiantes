from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import PersonApiView, DocenteApiView

urlpatterns = [
    path('', views.home, name='home'),  # Esto debe estar definido en views.py
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('welcome/', views.welcome, name='welcome'),

    path('cedulas/', views.PersonView.as_view(), name='cedulas'),
    path('cedulas/editar/<int:id>/', views.UpdatePersonView.as_view(), name='editar_persona'),
    path('cedulas/eliminar/<int:id>/', views.DeletePersonView.as_view(), name='eliminar_persona'),
    path('docentes/', views.DocenteView.as_view(), name='docentes'),
    path('docentes/editar/<int:id>/', views.UpdateDocenteView.as_view(), name='editar_docente'),
    path('cedulas/api/<int:id>/', PersonApiView.as_view(), name='person_api'),
    path('docentes/api/<int:id>/', DocenteApiView.as_view(), name='docente_api'),
    path('docentes/eliminar/<int:id>/', views.DeleteDocenteView.as_view(), name='eliminar_docente'),
    path('usuarios/', views.UserView.as_view(), name='usuarios'),
    path('usuarios/editar/<int:id>/', views.UpdateUserView.as_view(), name='editar_usuario'),
    path('usuarios/eliminar/<int:id>/', views.DeleteUserView.as_view(), name='eliminar_usuario'),
    path('todolist/', views.TodoListView.as_view(), name='todolist'),
    path('todolist/update/<int:id>/', views.UpdateTodoView.as_view(), name='update_todo'),
    path('todolist/delete/<int:id>/', views.DeleteTodoView.as_view(), name='delete_todo'),
    path('cursos/', views.CourseView.as_view(), name='cursos'),
    path('cursos/editar/<int:id>/', views.UpdateCourseView.as_view(), name='editar_curso'),
    path('cursos/eliminar/<int:id>/', views.DeleteCourseView.as_view(), name='eliminar_curso'),
    path('cursos/<int:course_id>/niveles/', views.LevelView.as_view(), name='niveles'),
    path('niveles/editar/<int:id>/', views.UpdateLevelView.as_view(), name='editar_nivel'),
    path('niveles/eliminar/<int:id>/', views.DeleteLevelView.as_view(), name='eliminar_nivel'),

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
