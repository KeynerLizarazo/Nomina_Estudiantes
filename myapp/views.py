from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Cedula, User, Calendario, Courses, Tutors, Levels, TodoItem
from .forms import CourseForm, LevelForm, TodoItemForm
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse_lazy
from functools import wraps
import json
import re
import pytz
from datetime import datetime

# ==============================
# Función home - Redirigir raíz a login o welcome
# ==============================
def home(request):
    if request.user.is_authenticated:
        return redirect('welcome')
    else:
        return redirect('login')


# ==============================
# Decorador personalizado para login requerido
# ==============================
def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def tutor_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or (request.user.role not in ['tutor', 'admin']):
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('welcome')
        return view_func(request, *args, **kwargs)
    return wrapper


# ==============================
# Funciones CRUD para Cédulas
# ==============================

@login_required
def welcome(request):
    
    return render(request, 'welcome.html')

class CourseView(LoginRequiredMixin, View):
    template_name = 'cursos.html'
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        form = CourseForm()
        courses = Courses.objects.all()
        tutors = Tutors.objects.all()
        context = {
            'form': form,
            'courses': courses,
            'tutors': tutors
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso agregado exitosamente.')
            return redirect('cursos')
        else:
            courses = Courses.objects.all()
            tutors = Tutors.objects.all()
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'courses': courses,
                'tutors': tutors
            }
            return render(request, self.template_name, context)

class UpdateCourseView(LoginRequiredMixin, View):
    template_name = 'cursos.html'
    login_url = 'login'

    def get(self, request, id, *args, **kwargs):
        course = get_object_or_404(Courses, id=id)
        form = CourseForm(instance=course)
        courses = Courses.objects.all()
        context = {
            'form': form,
            'courses': courses,
            'course_to_edit': course
        }
        return render(request, self.template_name, context)

    def post(self, request, id, *args, **kwargs):
        course = get_object_or_404(Courses, id=id)
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado exitosamente.')
            return redirect('cursos')
        else:
            courses = Courses.objects.all()
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'courses': courses,
                'course_to_edit': course
            }
            return render(request, self.template_name, context)

class DeleteCourseView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, id, *args, **kwargs):
        course = get_object_or_404(Courses, id=id)
        course.delete()
        messages.success(request, 'Curso eliminado exitosamente.')
        return redirect('cursos')

class LevelView(LoginRequiredMixin, View):
    template_name = 'niveles.html'
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        form = LevelForm()
        levels = Levels.objects.all()
        courses = Courses.objects.all()
        context = {
            'form': form,
            'levels': levels,
            'courses': courses
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = LevelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nivel agregado exitosamente.')
            return redirect('niveles')
        else:
            levels = Levels.objects.all()
            courses = Courses.objects.all()
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'levels': levels,
                'courses': courses
            }
            return render(request, self.template_name, context)

class UpdateLevelView(LoginRequiredMixin, View):
    template_name = 'niveles.html'
    login_url = 'login'

    def get(self, request, id, *args, **kwargs):
        level = get_object_or_404(Levels, id=id)
        form = LevelForm(instance=level)
        levels = Levels.objects.all()
        context = {
            'form': form,
            'levels': levels,
            'level_to_edit': level
        }
        return render(request, self.template_name, context)

    def post(self, request, id, *args, **kwargs):
        level = get_object_or_404(Levels, id=id)
        form = LevelForm(request.POST, instance=level)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nivel actualizado exitosamente.')
            return redirect('niveles')
        else:
            levels = Levels.objects.all()
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'levels': levels,
                'level_to_edit': level
            }
            return render(request, self.template_name, context)

class DeleteLevelView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, id, *args, **kwargs):
        level = get_object_or_404(Levels, id=id)
        level.delete()
        messages.success(request, 'Nivel eliminado exitosamente.')
        return redirect('niveles')

class TodoListView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'todolist.html'
    login_url = 'login'

    def test_func(self):
        return self.request.user.role in ['tutor', 'admin']

    def get(self, request, *args, **kwargs):
        form = TodoItemForm()
        tasks = TodoItem.objects.filter(user=request.user)
        context = {
            'form': form,
            'tasks': tasks
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = TodoItemForm(request.POST)
        if form.is_valid():
            todo_item = form.save(commit=False)
            todo_item.user = request.user
            todo_item.save()
            messages.success(request, 'Tarea agregada exitosamente.')
            return redirect('todolist')
        else:
            tasks = TodoItem.objects.filter(user=request.user)
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'tasks': tasks
            }
            return render(request, self.template_name, context)

class UpdateTodoView(LoginRequiredMixin, View):
    def post(self, request, id, *args, **kwargs):
        todo_item = get_object_or_404(TodoItem, id=id, user=request.user)
        todo_item.completed = not todo_item.completed
        todo_item.save()
        return redirect('todolist')

class DeleteTodoView(LoginRequiredMixin, View):
    def post(self, request, id, *args, **kwargs):
        todo_item = get_object_or_404(TodoItem, id=id, user=request.user)
        todo_item.delete()
        messages.success(request, 'Tarea eliminada exitosamente.')
        return redirect('todolist')

@login_required
def test_zone(request):

    return render(request, 'test_zone.html')

@login_required
def cedulas(request):
    """
    Vista principal para mostrar y filtrar registros de cédulas.
    Incluye búsqueda y filtro opcional por tipo_documento.
    """
    query = request.GET.get('q', '').strip()
    campo = request.GET.get('campo', '').strip()
    tipo_documento = request.GET.get('tipo_documento', 'todos')  # Nuevo parámetro
    cedula_obj = None

    if request.GET.get('editar'):
        cedula_id = request.GET.get('editar')
        cedula_obj = get_object_or_404(Cedula, id=cedula_id)

    # Iniciar queryset base
    cedulas_list = Cedula.objects.all()

    # Filtrar por tipo_documento
    if tipo_documento != 'todos':
        cedulas_list = cedulas_list.filter(tipo_documento=tipo_documento)

    # Aplicar búsqueda si hay término
    if query:
        if campo and campo != "todos":
            kwargs = {f"{campo}__icontains": query}
            cedulas_list = cedulas_list.filter(**kwargs)
        else:
            cedulas_list = cedulas_list.filter(
                Q(nombre__icontains=query) |
                Q(apellido__icontains=query) |
                Q(numero_documento__icontains=query) |
                Q(tipo_documento__icontains=query)
            )

    response = render(request, 'cedulas.html', {
        'cedulas': cedulas_list,
        'cedula_obj': cedula_obj,
        'query': query,
        'campo': campo,
        'tipo_documento': tipo_documento,
    })

    # Prevenir almacenamiento en caché del navegador
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


def guardar_cedula(request):
    """
    Guarda o actualiza un registro de cédula desde el formulario.
    """
    if request.method == 'POST':
        cedula_id = request.POST.get('id')
        tipo_documento = request.POST.get('tipo_documento')
        numero_documento = request.POST.get('numero_documento', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()

        # Validaciones básicas
        if not tipo_documento or tipo_documento not in ['V', 'CC']:
            messages.error(request, 'Tipo de documento inválido.')
            return redirect('cedulas')
        if not numero_documento.isdigit() or len(numero_documento) > 10:
            messages.error(request, 'Número de documento inválido.')
            return redirect('cedulas')
        if len(nombre) > 50 or len(apellido) > 50:
            messages.error(request, 'El nombre o apellido excede los 50 caracteres.')
            return redirect('cedulas')

        try:
            if cedula_id:  # Editando
                cedula = get_object_or_404(Cedula, id=cedula_id)
                cedula.tipo_documento = tipo_documento
                cedula.numero_documento = numero_documento
                cedula.nombre = nombre
                cedula.apellido = apellido
                cedula.save()
                messages.success(request, 'Registro actualizado correctamente.')
            else:  # Creando
                if Cedula.objects.filter(numero_documento=numero_documento).exists():
                    messages.error(request, 'El número de documento ya está registrado.')
                    return redirect('cedulas')
                Cedula.objects.create(
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    nombre=nombre,
                    apellido=apellido
                )
                messages.success(request, 'Registro guardado correctamente.')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al guardar: {str(e)}')

    return redirect('cedulas')


def eliminar_cedula(request, id):
    """
    Elimina un registro de cédula.
    """
    if request.method == 'POST':
        try:
            cedula = get_object_or_404(Cedula, id=id)
            cedula.delete()
            messages.success(request, "Registro eliminado correctamente.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al eliminar: {str(e)}")
    return redirect('cedulas')


# ==============================
# Funciones de Autenticación
# ==============================
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('welcome')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return redirect('login')

    return render(request, 'login.html')


def logout_view(request):
    """
    Cierra la sesión del usuario.
    """
    logout(request)
    return redirect('login')


# ==============================
# Vistas del Calendario
# ==============================
# @login_required
# def calendario_view(request):
#     """
#     Muestra el calendario con eventos registrados.
#     """
#     if request.method == 'POST':
#         form = CalendarioForm(request.POST)
#         if form.is_valid():
#             calendario = form.save(commit=False)
#             calendario.creador = request.user if request.user.is_authenticated else None
#             calendario.save()
#             return redirect('calendario')
#     else:
#         form = CalendarioForm()

#     eventos = Calendario.objects.all()
#     context = {
#         'form': form,
#         'eventos': eventos
#     }
#     return render(request, 'calendario.html', context)

# def agregar_evento(request):
#     if request.method == 'POST':
#         form = CalendarioForm(request.POST)
#         if form.is_valid():
#             evento = form.save(commit=False)
#             evento.creador = request.user
#             evento.save()
#             return redirect('calendario')
#     else:
#         form = CalendarioForm()

#     return render(request, 'calendario.html', {'form': form})


# @csrf_exempt
# def guardar_evento(request):
#     """
#     Guarda un evento nuevo en el calendario (AJAX).
#     """
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             tz = pytz.UTC  # Puedes cambiar a otra zona horaria si es necesario

#             evento = Calendario(
#                 titulo=data['titulo'],
#                 descripcion=data.get('descripcion'),
#                 fecha_inicio=tz.localize(datetime.fromisoformat(data['fecha_inicio'])),
#                 fecha_fin=tz.localize(datetime.fromisoformat(data['fecha_fin'])) if data.get('fecha_fin') else None,
#                 creador=request.user if request.user.is_authenticated else None
#             )
#             evento.save()
#             return JsonResponse({'success': True, 'id': evento.id})
#         except KeyError as e:
#             return JsonResponse({'success': False, 'error': f'Campo faltante: {e}'}, status=400)
#         except ValueError as e:
#             return JsonResponse({'success': False, 'error': 'Formato de fecha inválido.'}, status=400)
#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)}, status=500)

#     return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)


# @csrf_exempt
# def modificar_evento(request, evento_id):
    # try:
    #     evento_id = int(evento_id)
    # except ValueError:
    #     return JsonResponse({'success': False, 'error': 'ID inválido'}, status=400)

    # if request.method == 'POST':
    #     try:
    #         data = json.loads(request.body)
    #         evento = Calendario.objects.get(id=evento_id)

    #         # Validar y parsear fechas con zona horaria
    #         tz = pytz.UTC  # Puedes cambiarlo si usas una zona horaria específica

    #         fecha_inicio = data.get('fecha_inicio')
    #         if not fecha_inicio:
    #             return JsonResponse({'success': False, 'error': 'Fecha de inicio requerida'}, status=400)

    #         # Convertir fecha_inicio a datetime aware
    #         evento.fecha_inicio = tz.localize(datetime.fromisoformat(fecha_inicio))

    #         fecha_fin = data.get('fecha_fin')
    #         if fecha_fin:
    #             evento.fecha_fin = tz.localize(datetime.fromisoformat(fecha_fin))
    #         else:
    #             evento.fecha_fin = None

    #         # Guardar otros campos
    #         evento.titulo = data.get('titulo', evento.titulo)
    #         evento.descripcion = data.get('descripcion', evento.descripcion)
    #         evento.save()

    #         return JsonResponse({'success': True})
    #     except Calendario.DoesNotExist:
    #         return JsonResponse({'success': False, 'error': 'Evento no encontrado'}, status=404)
    #     except Exception as e:
    #         return JsonResponse({'success': False, 'error': str(e)}, status=500)
    # return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)
    
    
    
#     """
#     Modifica un evento existente (AJAX).
#     """
#     try:
#         evento_id = int(evento_id)
#     except ValueError:
#         return JsonResponse({'success': False, 'error': 'ID inválido'}, status=400)

#     try:
#         evento = Calendario.objects.get(id=evento_id)
#     except Calendario.DoesNotExist:
#         return JsonResponse({'success': False, 'error': 'Evento no encontrado'}, status=404)

#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             tz = pytz.UTC

#             if 'titulo' not in data:
#                 return JsonResponse({'success': False, 'error': 'Título es obligatorio.'}, status=400)

#             evento.titulo = data['titulo']
#             evento.descripcion = data.get('descripcion')

#             fecha_inicio = data.get('fecha_inicio')
#             if not fecha_inicio:
#                 return JsonResponse({'success': False, 'error': 'Fecha de inicio es obligatoria.'}, status=400)

#             evento.fecha_inicio = tz.localize(datetime.fromisoformat(fecha_inicio))
#             fecha_fin = data.get('fecha_fin')

#             if fecha_fin:
#                 evento.fecha_fin = tz.localize(datetime.fromisoformat(fecha_fin))
#             else:
#                 evento.fecha_fin = None

#             evento.save()
#             return JsonResponse({'success': True})

#         except KeyError as e:
#             return JsonResponse({'success': False, 'error': f'Campo faltante: {e}'}, status=400)
#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)}, status=500)

#     return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)


# @csrf_exempt
# def eliminar_evento(request, evento_id):
#     """
#     Elimina un evento del calendario (AJAX).
#     """
#     if request.method == 'DELETE':
#         try:
#             evento = Calendario.objects.get(id=evento_id)
#             evento.delete()
#             return JsonResponse({'success': True})
#         except Calendario.DoesNotExist:
#             return JsonResponse({'success': False, 'error': 'Evento no encontrado.'}, status=404)
#     return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)


# def eventos_json(request):
#     """
#     Devuelve todos los eventos en formato JSON para FullCalendar.
#     """
#     eventos = Calendario.objects.all()
#     data = [
#         {
#             'id': e.id,
#             'title': e.titulo,
#             'start': e.fecha_inicio.isoformat(),
#             'end': e.fecha_fin.isoformat() if e.fecha_fin else None,
#             'description': e.descripcion
#         }
#         for e in eventos
#     ]
#     return JsonResponse(data, safe=False)
