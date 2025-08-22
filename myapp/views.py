from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Cedula, User, Calendario, Courses, Tutors, Levels, TodoItem, Person
from .forms import CourseForm, LevelForm, PersonForm, TodoItemForm, UserForm, UserUpdateForm
from django.utils import timezone
from django.db import transaction
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


@login_required
def docentes(request):

    return render(request, 'docentes.html')

class UserView(LoginRequiredMixin, View):
    template_name = 'usuarios.html'
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        form = UserForm()
        users = User.objects.all()
        persons = Person.objects.all()
        
        query = request.GET.get('q')
        role = request.GET.get('role')

        if query:
            users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
        
        if role:
            users = users.filter(role=role)

        context = {
            'form': form,
            'users': users,
            'persons': persons,
            'query': query,
            'role': role
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Usuario agregado exitosamente.')
            return redirect('usuarios')
        else:
            users = User.objects.all()
            persons = Person.objects.all()
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'users': users,
                'persons': persons
            }
            return render(request, self.template_name, context)

class UpdateUserView(LoginRequiredMixin, View):
    template_name = 'usuarios.html'
    login_url = 'login'

    def post(self, request, id, *args, **kwargs):
        user = get_object_or_404(User, id=id)
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            password = request.POST.get('password')
            if password:
                user.set_password(password)
            user.save()
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('usuarios')
        else:
            users = User.objects.all()
            persons = Person.objects.all()
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'users': users,
                'persons': persons,
                'user_to_edit': user
            }
            return render(request, self.template_name, context)

class DeleteUserView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, id, *args, **kwargs):
        user = get_object_or_404(User, id=id)
        user.delete()
        messages.success(request, 'Usuario eliminado exitosamente.')
        return redirect('usuarios')


class PersonView(LoginRequiredMixin, View):
    template_name = 'cedulas.html'
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        form = PersonForm()
        persons = Person.objects.all()
        
        query = request.GET.get('q')
        campo = request.GET.get('campo')

        if query:
            if campo and campo != "todos":
                filter_kwargs = {f"{campo}__icontains": query}
                persons = persons.filter(**filter_kwargs)
            else:
                persons = persons.filter(
                    Q(name__icontains=query) |
                    Q(surname__icontains=query) |
                    Q(document_number__icontains=query) |
                    Q(email__icontains=query)
                )

        context = {
            'form': form,
            'persons': persons,
            'query': query,
            'campo': campo
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = PersonForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Guardar la persona
                    person = form.save()

                    # Crear el usuario asociado
                    user = User.objects.create_user(
                        username=person.document_number,
                        password=person.document_number,
                        email=person.email,
                        documento=person.document_number,
                        role='student',
                        person=person
                    )
                    user.first_name = person.name
                    user.last_name = person.surname
                    user.save()

                    messages.success(request, 'Estudiante agregado exitosamente.')
                    return redirect('cedulas')
            except Exception as e:
                messages.error(request, f'Ocurrió un error al crear el usuario: {e}')
                persons = Person.objects.all()
                context = {
                    'form': form,
                    'persons': persons
                }
                return render(request, self.template_name, context)
        else:
            persons = Person.objects.all()
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'persons': persons
            }
            return render(request, self.template_name, context)


class UpdatePersonView(LoginRequiredMixin, View):
    template_name = 'cedulas.html'
    login_url = 'login'

    def post(self, request, id, *args, **kwargs):
        person = get_object_or_404(Person, id=id)
        form = PersonForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            messages.success(request, 'Persona actualizada exitosamente.')
            return redirect('cedulas')
        else:
            persons = Person.objects.all()
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'persons': persons,
                'person_to_edit': person
            }
            return render(request, self.template_name, context)


class DeletePersonView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, id, *args, **kwargs):
        person = get_object_or_404(Person, id=id)
        person.delete()
        messages.success(request, 'Persona eliminada exitosamente.')
        return redirect('cedulas')

class CourseView(LoginRequiredMixin, View):
    template_name = 'cursos.html'
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        form = CourseForm()
        courses = Courses.objects.all()
        tutors = Tutors.objects.all()
        
        query = request.GET.get('q')
        if query:
            courses = courses.filter(course_name__icontains=query)

        context = {
            'form': form,
            'courses': courses,
            'tutors': tutors,
            'query': query
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

    def get(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Courses, id=course_id)
        form = LevelForm(initial={'course': course})
        levels = Levels.objects.filter(course=course)
        
        query = request.GET.get('q')
        if query:
            levels = levels.filter(level_name__icontains=query)

        context = {
            'form': form,
            'levels': levels,
            'course': course,
            'query': query
        }
        return render(request, self.template_name, context)

    def post(self, request, course_id, *args, **kwargs):
        course = get_object_or_404(Courses, id=course_id)
        form = LevelForm(request.POST)
        if form.is_valid():
            level = form.save(commit=False)
            level.course = course
            level.save()
            messages.success(request, 'Nivel agregado exitosamente.')
            return redirect('niveles', course_id=course_id)
        else:
            levels = Levels.objects.filter(course=course)
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'levels': levels,
                'course': course
            }
            return render(request, self.template_name, context)

class UpdateLevelView(LoginRequiredMixin, View):
    template_name = 'niveles.html'
    login_url = 'login'

    def get(self, request, id, *args, **kwargs):
        level = get_object_or_404(Levels, id=id)
        course = level.course
        form = LevelForm(instance=level)
        levels = Levels.objects.filter(course=course)
        context = {
            'form': form,
            'levels': levels,
            'level_to_edit': level,
            'course': course
        }
        return render(request, self.template_name, context)

    def post(self, request, id, *args, **kwargs):
        level = get_object_or_404(Levels, id=id)
        course = level.course
        form = LevelForm(request.POST, instance=level)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nivel actualizado exitosamente.')
            return redirect('niveles', course_id=course.id)
        else:
            levels = Levels.objects.filter(course=course)
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'levels': levels,
                'level_to_edit': level,
                'course': course
            }
            return render(request, self.template_name, context)

class DeleteLevelView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, id, *args, **kwargs):
        level = get_object_or_404(Levels, id=id)
        course_id = level.course.id
        level.delete()
        messages.success(request, 'Nivel eliminado exitosamente.')
        return redirect('niveles', course_id=course_id)

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


# INTENTO DE BACKEND DE GABO !!!!

class DocenteView(LoginRequiredMixin, View):
    template_name = 'docentes.html'
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        form = PersonForm()
        # Filtrar solo docentes: puedes ajustar el valor del campo `position`
        persons = Person.objects.filter(position__icontains='docente')  # Cambia si usas un valor específico

        # O si prefieres mostrar todos pero destacar los docentes, quita el filtro arriba

        query = request.GET.get('q')
        campo = request.GET.get('campo')

        if query:
            if campo and campo != "todos":
                filter_kwargs = {f"{campo}__icontains": query}
                persons = persons.filter(**filter_kwargs)
            else:
                persons = persons.filter(
                    Q(name__icontains=query) |
                    Q(surname__icontains=query) |
                    Q(document_number__icontains=query) |
                    Q(email__icontains=query) |
                    Q(position__icontains=query)
                )

        context = {
            'form': form,
            'persons': persons,
            'query': query,
            'campo': campo
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = PersonForm(request.POST)
        if form.is_valid():
            person = form.save(commit=False)
            # Aseguramos que el cargo sea "Docente" si es necesario
            # person.position = "Docente"  # descomenta si quieres forzarlo
            person.save()
            messages.success(request, 'Docente agregado exitosamente.')
            return redirect('docentes')
        else:
            # Mantener el filtro en caso de error
            persons = Person.objects.filter(position__icontains='docente')
            query = request.GET.get('q')
            campo = request.GET.get('campo')
            if query:
                if campo and campo != "todos":
                    filter_kwargs = {f"{campo}__icontains": query}
                    persons = persons.filter(**filter_kwargs)
                else:
                    persons = persons.filter(
                        Q(name__icontains=query) |
                        Q(surname__icontains=query) |
                        Q(document_number__icontains=query) |
                        Q(email__icontains=query)
                    )
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'persons': persons,
                'query': query,
                'campo': campo
            }
            return render(request, self.template_name, context)
class UpdateDocenteView(LoginRequiredMixin, View):
    template_name = 'docentes.html'
    login_url = 'login'

    def post(self, request, id, *args, **kwargs):
        person = get_object_or_404(Person, id=id)
        form = PersonForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            messages.success(request, 'Docente actualizado exitosamente.')
            return redirect('docentes')
        else:
            persons = Person.objects.filter(position__icontains='docente')
            query = request.GET.get('q')
            campo = request.GET.get('campo')
            if query:
                if campo and campo != "todos":
                    filter_kwargs = {f"{campo}__icontains": query}
                    persons = persons.filter(**filter_kwargs)
                else:
                    persons = persons.filter(
                        Q(name__icontains=query) |
                        Q(surname__icontains=query) |
                        Q(document_number__icontains=query) |
                        Q(email__icontains=query)
                    )
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'persons': persons,
                'person_to_edit': person,
                'query': query,
                'campo': campo
            }
            return render(request, self.template_name, context)
        
class DeleteDocenteView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, id, *args, **kwargs):
        person = get_object_or_404(Person, id=id)
        person.delete()
        messages.success(request, 'Docente eliminado exitosamente.')
        return redirect('docentes')

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
