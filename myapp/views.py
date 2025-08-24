from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
# Endpoint para obtener datos de una persona en JSON para el modal AJAX
# Vista basada en clase para API de persona (AJAX)
from django.views import View
from django.http import JsonResponse
###################################
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Cedula, User, Calendario, Courses, Tutors, Levels, TodoItem, Person
from .forms import CourseForm, LevelForm, PersonForm, TodoItemForm, UserForm, UserUpdateForm, DocenteForm
from .models import User
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

    def get(self, request, id, *args, **kwargs):
        user = get_object_or_404(User, id=id)
        form = UserUpdateForm(instance=user)
        users = User.objects.all()
        persons = Person.objects.all()
        context = {
            'form': form,
            'users': users,
            'persons': persons,
            'user_to_edit': user
        }
        return render(request, self.template_name, context)

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

class PersonApiView(View):
    def get(self, request, id, *args, **kwargs):
        person = get_object_or_404(Person, id=id)
        data = {
            'type_document': person.type_document,
            'document_number': person.document_number,
            'name': person.name,
            'surname': person.surname,
            'telephone_number': person.telephone_number,
            'email': person.email,
            'date_of_birth': person.date_of_birth.strftime('%Y-%m-%d') if person.date_of_birth else '',
            'gender': person.gender,
            'nationality': person.nationality,
            'progenitor_document_number': person.progenitor_document_number,
            'progenitor_name': person.progenitor_name,
        }
        return JsonResponse(data)
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
                        role='estudiante',
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

    def get(self, request, id, *args, **kwargs):
        person = get_object_or_404(Person, id=id)
        form = PersonForm(instance=person)
        persons = Person.objects.all()
        context = {
            'form': form,
            'persons': persons,
            'person_to_edit': person
        }
        return render(request, self.template_name, context)

    def post(self, request, id, *args, **kwargs):
        person = get_object_or_404(Person, id=id)
        form = PersonForm(request.POST, instance=person)
        if form.is_valid():
            person = form.save()
            # Sincronizar datos con el usuario relacionado (si existe)
            from .models import User
            try:
                user = User.objects.get(person=person)
                user.email = person.email or ''
                user.first_name = person.name or ''
                user.last_name = person.surname or ''
                user.save()
            except User.DoesNotExist:
                pass
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
class DocenteApiView(View):
    def get(self, request, id, *args, **kwargs):
        from .models import Tutors
        tutor = get_object_or_404(Tutors, id=id)
        person = tutor.person
        data = {
            'type_document': person.type_document,
            'document_number': person.document_number,
            'name': person.name,
            'surname': person.surname,
            'telephone_number': person.telephone_number,
            'email': person.email,
            'date_of_birth': person.date_of_birth.strftime('%Y-%m-%d') if person.date_of_birth else '',
            'gender': person.gender,
            'nationality': person.nationality,
            'staff_position': tutor.staff_position,
        }
        return JsonResponse(data)

class DocenteView(LoginRequiredMixin, View):
    template_name = 'docentes.html'
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        form = DocenteForm()
        tutors = Tutors.objects.all()
        
        query = request.GET.get('q')
        campo = request.GET.get('campo')

        if query:
            if campo and campo != "todos":
                filter_kwargs = {f"person__{campo}__icontains": query}
                tutors = tutors.filter(**filter_kwargs)
            else:
                tutors = tutors.filter(
                    Q(person__name__icontains=query) |
                    Q(person__surname__icontains=query) |
                    Q(person__document_number__icontains=query) |
                    Q(person__email__icontains=query)
                )

        context = {
            'form': form,
            'tutors': tutors,
            'query': query,
            'campo': campo
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = DocenteForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear la persona
                    person = Person.objects.create(
                        type_document=form.cleaned_data['type_document'],
                        document_number=form.cleaned_data['document_number'],
                        name=form.cleaned_data['name'],
                        surname=form.cleaned_data['surname'],
                        telephone_number=form.cleaned_data['telephone_number'],
                        email=form.cleaned_data['email'],
                        date_of_birth=form.cleaned_data['date_of_birth'],
                        gender=form.cleaned_data['gender'],
                        nationality=form.cleaned_data['nationality']
                    )

                    # Crear el usuario asociado
                    user = User.objects.create_user(
                        username=person.document_number,
                        password=person.document_number,
                        email=person.email,
                        documento=person.document_number,
                        role='tutor',
                        person=person
                    )
                    user.first_name = person.name
                    user.last_name = person.surname
                    user.save()

                    # Crear el tutor
                    Tutors.objects.create(
                        person=person,
                        user=user,
                        staff_position=form.cleaned_data['staff_position']
                    )

                    messages.success(request, 'Docente agregado exitosamente.')
                    return redirect('docentes')
            except Exception as e:
                messages.error(request, f'Ocurrió un error al crear el docente: {e}')
                tutors = Tutors.objects.all()
                context = {
                    'form': form,
                    'tutors': tutors
                }
                return render(request, self.template_name, context)
        else:
            tutors = Tutors.objects.all()
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'tutors': tutors
            }
            return render(request, self.template_name, context)
class UpdateDocenteView(LoginRequiredMixin, View):
    template_name = 'docentes.html'
    login_url = 'login'

    def get(self, request, id, *args, **kwargs):
        tutor = get_object_or_404(Tutors, id=id)
        person = tutor.person
        form = DocenteForm(instance=person, initial={'staff_position': tutor.staff_position})
        tutors = Tutors.objects.all()
        context = {
            'form': form,
            'tutors': tutors,
            'tutor_to_edit': tutor
        }
        return render(request, self.template_name, context)

    def post(self, request, id, *args, **kwargs):
        tutor = get_object_or_404(Tutors, id=id)
        person = tutor.person
        form = DocenteForm(request.POST, instance=person)
        if form.is_valid():
            person = form.save()
            tutor.staff_position = request.POST.get('staff_position')
            tutor.save()
            # Sincronizar datos con el usuario relacionado (si existe)
            try:
                user = User.objects.get(person=person)
                user.email = person.email or ''
                user.first_name = person.name or ''
                user.last_name = person.surname or ''
                user.save()
            except User.DoesNotExist:
                pass
            messages.success(request, 'Docente actualizado exitosamente.')
            return redirect('docentes')
        else:
            tutors = Tutors.objects.all()
            messages.error(request, 'Por favor corrija los errores en el formulario.')
            context = {
                'form': form,
                'tutors': tutors,
                'tutor_to_edit': tutor
            }
            return render(request, self.template_name, context)
        
class DeleteDocenteView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, id, *args, **kwargs):
        tutor = get_object_or_404(Tutors, id=id)
        tutor.delete()
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
