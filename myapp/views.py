from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import update_session_auth_hash
from django.db.models import CharField
from django.db.models.functions import Cast
from django.views import View
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404

from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Cedula, User, Calendario, Courses, Tutors, Levels, TodoItem, Person
from .forms import CourseForm, LevelForm, PersonForm, TodoItemForm, UserForm, UserUpdateForm, DocenteForm, UnitForm
from .models import Person, Students, User, Units
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, CharField
from django.db.models.functions import Cast
from django.urls import reverse_lazy
from functools import wraps
import json
import re
import pytz
from datetime import datetime
""""""
from django.contrib.postgres.search import TrigramSimilarity 
# Extensión de PostgreSQL que permite filtrar datos de búsqueda de forma sensible
""""""
import os
import uuid
from django.http import JsonResponse

from django.conf import settings
from PIL import Image
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


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
    
    must_change_password = request.session.get('must_change_password', False)
    return render(request, 'welcome.html', {'must_change_password': must_change_password})


@login_required
def docentes(request):

    return render(request, 'docentes.html')

class SeccionView(LoginRequiredMixin, View):
    template_name = 'secciones.html'
    login_url = 'login'

    def get(self, request, level_id, *args, **kwargs):
        level = get_object_or_404(Levels, id=level_id)
        course = level.course
        units = level.units.order_by('topic_order')
        context = {
            'level': level,
            'course': course,
            'units': units
        }
        return render(request, self.template_name, context)

class UpdateUnitOrderView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            order_data = data.get('order', [])
            with transaction.atomic():
                for item in order_data:
                    unit_id = item.get('id')
                    order = item.get('order')
                    if unit_id is not None and order is not None:
                        unit = get_object_or_404(Units, id=unit_id)
                        unit.topic_order = order
                        unit.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

class CreateUnitView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, level_id, *args, **kwargs):
        try:
            level = get_object_or_404(Levels, id=level_id)
            
            # Obtener el último `topic_order` y sumarle 1
            last_unit = Units.objects.filter(level=level).order_by('-topic_order').first()
            new_order = (last_unit.topic_order + 1) if last_unit else 1
            
            unit = Units.objects.create(
                title=request.POST.get('material_title'),
                content=request.POST.get('material_content'),
                pdf_material=request.FILES.get('material_pdf'),
                level=level,
                topic_order=new_order
            )
            
            return JsonResponse({
                'status': 'success',
                'unit': {
                    'id': unit.id,
                    'name': unit.title,
                    'topic_order': unit.topic_order
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

class UnitJsonView(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request, unit_id, *args, **kwargs):
        unit = get_object_or_404(Units, id=unit_id)
        pdf_filename = ''
        if unit.pdf_material:
            pdf_filename = unit.pdf_material.name.split('/')[-1]

        return JsonResponse({
            'id': unit.id,
            'name': unit.title,
            'description': unit.content,
            'pdf_material_url': unit.pdf_material.url if unit.pdf_material else None,
            'pdf_filename': pdf_filename
        })

class UpdateUnitView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, unit_id, *args, **kwargs):
        try:
            unit = get_object_or_404(Units, id=unit_id)
            unit.title = request.POST.get('material_title')
            unit.content = request.POST.get('material_content')
            
            if 'material_pdf' in request.FILES:
                unit.pdf_material = request.FILES['material_pdf']
            
            unit.save()
            
            return JsonResponse({
                'status': 'success',
                'unit': {
                    'id': unit.id,
                    'name': unit.title,
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

class DeleteUnitView(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, unit_id, *args, **kwargs):
        unit = get_object_or_404(Units, id=unit_id)
        level_id = unit.level.id
        unit.delete()
        messages.success(request, 'Unidad eliminada exitosamente.')
        return redirect('secciones', level_id=level_id)

class UnitCreateView(LoginRequiredMixin, View):
    template_name = 'unit_form.html'
    login_url = 'login'

    def get(self, request, level_id):
        level = get_object_or_404(Levels, id=level_id)
        form = UnitForm()
        return render(request, self.template_name, {'form': form, 'level': level})

    def post(self, request, level_id):
        level = get_object_or_404(Levels, id=level_id)
        form = UnitForm(request.POST, request.FILES)
        if form.is_valid():
            unit = form.save(commit=False)
            unit.level = level
            last_unit = Units.objects.filter(level=level).order_by('-topic_order').first()
            unit.topic_order = (last_unit.topic_order + 1) if last_unit else 1
            unit.save()
            messages.success(request, 'Unidad agregada exitosamente.')
            return redirect('secciones', level_id=level.id)
        return render(request, self.template_name, {'form': form, 'level': level})

class UnitUpdateView(LoginRequiredMixin, View):
    template_name = 'unit_form.html'
    login_url = 'login'

    def get(self, request, unit_id):
        unit = get_object_or_404(Units, id=unit_id)
        level = unit.level
        form = UnitForm(instance=unit)
        return render(request, self.template_name, {'form': form, 'level': level, 'unit': unit})

    def post(self, request, unit_id):
        unit = get_object_or_404(Units, id=unit_id)
        level = unit.level
        form = UnitForm(request.POST, request.FILES, instance=unit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Unidad actualizada exitosamente.')
            return redirect('secciones', level_id=level.id)
        return render(request, self.template_name, {'form': form, 'level': level, 'unit': unit})

@csrf_exempt
@login_required
def change_password(request):
    if request.method == 'POST':
        user = request.user
        new_password = request.POST.get('new_password', '').strip()
        if not new_password or len(new_password) < 8:
            return JsonResponse({'success': False, 'error': 'La nueva contraseña debe tener al menos 8 caracteres.'})
        user.set_password(new_password)
        user.must_change_password = False
        user.save()
        update_session_auth_hash(request, user)  # Mantiene la sesión activa
        request.session['must_change_password'] = False  # Actualiza la sesión
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Método no permitido.'})
class UserView(LoginRequiredMixin, View):
    template_name = 'usuarios.html'
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        form = UserForm()
    # Mostrar solo usuarios activos
        users = User.all_objects.filter(is_deleted=False).only('id', 'username', 'email', 'documento', 'role')
        persons = Person.objects.all().only('id', 'name', 'surname', 'document_number')

        query = request.GET.get('q')
        role = request.GET.get('role')

        if query:
            # Mapeo de roles legibles a valores internos
            role_map = {
                'administrador': 'admin',
                'admin': 'admin',
                'profesor': 'profesor',
                'tutor': 'tutor',
                'estudiante': 'estudiante',
            }
            q_role = Q(role__icontains=query)
            if query.lower() in role_map:
                q_role = Q(role=role_map[query.lower()])
            if len(query) < 4:
                users = users.filter(
                    Q(username__icontains=query) |
                    Q(email__icontains=query) |
                    Q(documento__icontains=query) |
                    q_role
                )
            else:
                users = users.annotate(
                    sim_username=TrigramSimilarity('username', query),
                    sim_email=TrigramSimilarity('email', query),
                    sim_documento=TrigramSimilarity('documento', query),
                    sim_role=TrigramSimilarity('role', query),
                ).filter(
                    Q(sim_username__gt=0.3) |
                    Q(sim_email__gt=0.3) |
                    Q(sim_documento__gt=0.3) |
                    Q(sim_role__gt=0.3)
                ).order_by('-sim_username', '-sim_email', '-sim_documento', '-sim_role')

        if role:
            users = users.filter(role=role)

        # Paginación tradicional (10 registros por página)
        paginator = Paginator(users.order_by('id'), 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'form': form,
            'users': page_obj,
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
            error_list_html = ''.join([f'<li>{error}</li>' for error_list in form.errors.values() for error in error_list])
            error_string = f"<ul>{error_list_html}</ul>"
            messages.error(request, f"Por favor corrija los siguientes errores:{error_string}")
            users = User.objects.all()
            persons = Person.objects.all()
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
            error_list_html = ''.join([f'<li>{error}</li>' for error_list in form.errors.values() for error in error_list])
            error_string = f"<ul>{error_list_html}</ul>"
            messages.error(request, f"Por favor corrija los siguientes errores:{error_string}")
            users = User.objects.all()
            persons = Person.objects.all()
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
            'pais_origen': person.pais_origen,
            'progenitor_document_number': person.progenitor_document_number,
            'progenitor_name': person.progenitor_name,
        }
        return JsonResponse(data)
class PersonView(LoginRequiredMixin, View):
    def sync_students(self):
        # Solo crear Students para personas cuyo usuario tiene rol 'estudiante'
        existing_tutor_ids = set(Tutors.all_objects.values_list('person_id', flat=True))
        tutor_users = User.objects.filter(role__in=['profesor', 'tutor', 'administrador'], is_deleted=False)
        # Solo crear para personas que no tengan ningún registro de tutor (ni eliminado)
        missing_persons = Person.objects.filter(is_deleted=False, id__in=tutor_users.values_list('person_id', flat=True)).exclude(id__in=existing_tutor_ids)
        for p in missing_persons:
            user = tutor_users.filter(person=p).first()
            if user:
                Tutors.objects.create(
                    staff_position=user.role,
                    user=user,
                    person=p
                )
        """"""
        # existing_student_ids = set(Students.objects.values_list('person_id', flat=True))
        # student_users = User.objects.filter(role='estudiante', is_deleted=False)
        # missing_persons = Person.objects.filter(is_deleted=False, id__in=student_users.values_list('person_id', flat=True)).exclude(id__in=existing_student_ids)
        # for p in missing_persons:
        #     user = student_users.filter(person=p).first()
        #     if user:
        #         Students.objects.create(
        #             date_register=p.date_of_birth or timezone.now().date(),
        #             status='activo',
        #             user=user,
        #             person=p
        #         )
        """"""
    template_name = 'cedulas.html'
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        # Sincronizar estudiantes antes de mostrar
        self.sync_students()
        form = PersonForm()
        # Solo personas que son estudiantes (tienen registro en Students y usuario con rol estudiante)
        student_person_ids = set(Students.objects.filter(is_deleted=False).values_list('person_id', flat=True))
        student_users = set(User.objects.filter(role='estudiante', is_deleted=False).values_list('person_id', flat=True))
        ids = student_person_ids & student_users
        persons = Person.objects.filter(is_deleted=False, id__in=ids).only('id', 'name', 'surname', 'document_number', 'email')

        query = request.GET.get('q')
        campo = request.GET.get('campo')

        if query:
            if campo and campo != "todos":
                filter_kwargs = {f"{campo}__icontains": query}
                persons = persons.filter(**filter_kwargs)
            else:
                # Si la búsqueda es corta o es 'masculino'/'femenino', usar también icontains y mapear sexo
                if len(query) < 4 or query.lower() in ['masculino', 'femenino']:
                    gender_map = {
                        'masculino': 'M',
                        'femenino': 'F',
                        'm': 'M',
                        'f': 'F',
                    }
                    q_gender = Q(gender__icontains=query)
                    if query.lower() in gender_map:
                        q_gender = Q(gender=gender_map[query.lower()])
                    persons = persons.filter(
                        Q(name__icontains=query) |
                        Q(surname__icontains=query) |
                        Q(document_number__icontains=query) |
                        Q(email__icontains=query) |
                        Q(type_document__icontains=query) |
                        Q(telephone_number__icontains=query) |
                        q_gender |
                        Q(date_of_birth__icontains=query) |
                        Q(pais_origen__icontains=query) |
                        Q(progenitor_document_number__icontains=query) |
                        Q(progenitor_name__icontains=query)
                    )
                else:
                    persons = persons.annotate(
                        sim_name=TrigramSimilarity('name', query),
                        sim_surname=TrigramSimilarity('surname', query),
                        sim_document=TrigramSimilarity('document_number', query),
                        sim_email=TrigramSimilarity('email', query),
                        sim_type_document=TrigramSimilarity('type_document', query),
                        sim_telephone=TrigramSimilarity('telephone_number', query),
                        sim_gender=TrigramSimilarity('gender', query),
                        sim_birth=TrigramSimilarity(Cast('date_of_birth', CharField()), query),
                        sim_pais=TrigramSimilarity('pais_origen', query),
                        sim_progenitor_document=TrigramSimilarity('progenitor_document_number', query),
                        sim_progenitor_name=TrigramSimilarity('progenitor_name', query),
                    ).filter(
                        Q(sim_name__gt=0.3) |
                        Q(sim_surname__gt=0.3) |
                        Q(sim_document__gt=0.3) |
                        Q(sim_email__gt=0.3) |
                        Q(sim_type_document__gt=0.3) |
                        Q(sim_telephone__gt=0.3) |
                        Q(sim_gender__gt=0.3) |
                        Q(sim_birth__gt=0.3) |
                        Q(sim_pais__gt=0.3) |
                        Q(sim_progenitor_document__gt=0.3) |
                        Q(sim_progenitor_name__gt=0.3)
                    ).order_by(
                        '-sim_name', '-sim_surname', '-sim_document', '-sim_email', '-sim_type_document', '-sim_telephone', '-sim_gender', '-sim_birth', '-sim_pais', '-sim_progenitor_document', '-sim_progenitor_name'
                    )

        paginator = Paginator(persons.order_by('id'), 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'form': form,
            'persons': page_obj,
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
                        person=person,
                        must_change_password=True
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
            error_list_html = ''.join([f'<li>{error}</li>' for error_list in form.errors.values() for error in error_list])
            error_string = f"<ul>{error_list_html}</ul>"
            messages.error(request, f"Por favor corrija los siguientes errores:{error_string}")
            persons = Person.objects.all()
            context = {
                'form': form,
                'persons': persons,
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
            messages.success(request, 'Estudiante actualizado exitosamente.')
            return redirect('cedulas')
        else:
            error_list_html = ''.join([f'<li>{error}</li>' for error_list in form.errors.values() for error in error_list])
            error_string = f"<ul>{error_list_html}</ul>"
            messages.error(request, f"Por favor corrija los siguientes errores:{error_string}")
            persons = Person.objects.all()
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
        messages.success(request, 'Estudiante eliminada exitosamente.')
        return redirect('cedulas')

class CourseView(LoginRequiredMixin, View):
    template_name = 'cursos.html'
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        form = CourseForm()
        courses = Courses.objects.filter(is_deleted=False).only('id', 'course_name', 'tutor', 'deleted_at')
        tutors = Tutors.objects.filter(is_deleted=False).only('id', 'person', 'staff_position')

        query = request.GET.get('q')
        if query:
            courses = courses.filter(course_name__startswith=query)

        # Paginación por id
        last_id = request.GET.get('last_id')
        page_size = 20
        if last_id:
            courses = courses.filter(id__gt=last_id)
        courses = courses.order_by('id')[:page_size]

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
        levels = Levels.objects.filter(course=course).only('id', 'level_name', 'course')

        query = request.GET.get('q')
        if query:
            levels = levels.filter(level_name__startswith=query)

        # Paginación por id
        last_id = request.GET.get('last_id')
        page_size = 20
        if last_id:
            levels = levels.filter(id__gt=last_id)
        levels = levels.order_by('id')[:page_size]

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
        tasks = TodoItem.objects.filter(user=request.user).only('id', 'task', 'completed', 'due_date')

        # Paginación por id
        last_id = request.GET.get('last_id')
        page_size = 20
        if last_id:
            tasks = tasks.filter(id__gt=last_id)
        tasks = tasks.order_by('id')[:page_size]

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
            'pais_origen': person.pais_origen,
            'staff_position': tutor.staff_position,
        }
        return JsonResponse(data)

class DocenteView(LoginRequiredMixin, View):
    template_name = 'docentes.html'
    login_url = 'login'

    def sync_tutors(self):
        from .models import Person, Tutors, User
        existing_tutor_ids = set(Tutors.all_objects.values_list('person_id', flat=True))
        tutor_users = User.objects.filter(role__in=['profesor', 'tutor', 'administrador'], is_deleted=False)
        missing_persons = Person.objects.filter(is_deleted=False, id__in=tutor_users.values_list('person_id', flat=True)).exclude(id__in=existing_tutor_ids)
        for p in missing_persons:
            user = tutor_users.filter(person=p).first()
            if user:
                Tutors.objects.create(
                    staff_position=user.role,
                    user=user,
                    person=p
                )

    def get(self, request, *args, **kwargs):
        self.sync_tutors()
        form = DocenteForm()
        tutors = Tutors.objects.filter(is_deleted=False).only('id', 'person', 'staff_position')

        query = request.GET.get('q')
        campo = request.GET.get('campo')

        if query:
            if campo and campo != "todos":
                filter_kwargs = {f"person__{campo}__icontains": query}
                tutors = tutors.filter(**filter_kwargs)
            else:
                # Si la búsqueda es corta, usar también icontains
                if len(query) < 4 or query.lower() in ['masculino', 'femenino']:
                    gender_map = {
                        'masculino': 'M',
                        'femenino': 'F',
                        'm': 'M',
                        'f': 'F',
                    }
                    q_gender = Q(person__gender__icontains=query)
                    # Si el usuario escribe 'masculino' o 'femenino', buscar por 'M' o 'F' en la base de datos
                    if query.lower() in gender_map:
                        q_gender = Q(person__gender=gender_map[query.lower()])
                    tutors = tutors.filter(
                        Q(person__name__icontains=query) |
                        Q(person__surname__icontains=query) |
                        Q(person__document_number__icontains=query) |
                        Q(person__email__icontains=query) |
                        Q(person__type_document__icontains=query) |
                        Q(person__telephone_number__icontains=query) |
                        q_gender |
                        Q(person__date_of_birth__icontains=query) |
                        Q(person__pais_origen__icontains=query) |
                        Q(staff_position__icontains=query)
                    )
                else:
                    tutors = tutors.annotate(
                        sim_name=TrigramSimilarity('person__name', query),
                        sim_surname=TrigramSimilarity('person__surname', query),
                        sim_document=TrigramSimilarity('person__document_number', query),
                        sim_email=TrigramSimilarity('person__email', query),
                        sim_type_document=TrigramSimilarity('person__type_document', query),
                        sim_telephone=TrigramSimilarity('person__telephone_number', query),
                        sim_gender=TrigramSimilarity('person__gender', query),
                        sim_birth=TrigramSimilarity(Cast('person__date_of_birth', CharField()), query),
                        sim_pais=TrigramSimilarity('person__pais_origen', query),
                        sim_staff_position=TrigramSimilarity('staff_position', query),
                    ).filter(
                        Q(sim_name__gt=0.3) |
                        Q(sim_surname__gt=0.3) |
                        Q(sim_document__gt=0.3) |
                        Q(sim_email__gt=0.3) |
                        Q(sim_type_document__gt=0.3) |
                        Q(sim_telephone__gt=0.3) |
                        Q(sim_gender__gt=0.3) |
                        Q(sim_birth__gt=0.3) |
                        Q(sim_pais__gt=0.3) |
                        Q(sim_staff_position__gt=0.3)
                    ).order_by(
                        '-sim_name', '-sim_surname', '-sim_document', '-sim_email', '-sim_type_document', '-sim_telephone', '-sim_gender', '-sim_birth', '-sim_pais', '-sim_staff_position'
                    )

        paginator = Paginator(tutors.order_by('id'), 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'form': form,
            'tutors': page_obj,
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
                        pais_origen=form.cleaned_data['pais_origen']
                    )

                    # Crear el usuario asociado
                    user = User.objects.create_user(
                        username=person.document_number,
                        password=person.document_number,
                        email=person.email,
                        documento=person.document_number,
                        role='tutor',
                        person=person,
                        must_change_password=True
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
                tutors = Tutors.objects.filter(is_deleted=False)
                context = {
                    'form': form,
                    'tutors': tutors
                }
                return render(request, self.template_name, context)
        else:
            error_list_html = ''.join([f'<li>{error}</li>' for error_list in form.errors.values() for error in error_list])
            error_string = f"<ul>{error_list_html}</ul>"
            messages.error(request, f"Por favor corrija los siguientes errores:{error_string}")
            tutors = Tutors.objects.filter(is_deleted=False)
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
        tutors = Tutors.objects.filter(is_deleted=False)
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
            error_list_html = ''.join([f'<li>{error}</li>' for error_list in form.errors.values() for error in error_list])
            error_string = f"<ul>{error_list_html}</ul>"
            messages.error(request, f"Por favor corrija los siguientes errores:{error_string}")
            tutors = Tutors.objects.filter(is_deleted=False)
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
# Subida de imágenes para TinyMCE
# ==============================

@csrf_exempt
def upload_image(request):
    if request.method != 'POST' or not request.FILES.get('file'):
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    file = request.FILES['file']

    # Validar que es una imagen
    try:
        Image.open(file).verify()
        file.seek(0)
    except Exception:
        return JsonResponse({'error': 'Invalid image file.'}, status=400)

    # Generar nombre único
    ext = os.path.splitext(file.name)[1]
    filename = f"tinymce_{uuid.uuid4().hex}{ext}"
    path = os.path.join('tinymce', 'images', filename)

    # Guardar usando el sistema de almacenamiento predeterminado
    default_storage.save(path, ContentFile(file.read()))

    # Devolver la URL pública
    location = f'{settings.MEDIA_URL}{path}'
    return JsonResponse({'location': location})


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
            # Guardar en sesión si debe cambiar contraseña
            if hasattr(user, 'must_change_password') and user.must_change_password:
                request.session['must_change_password'] = True
            else:
                request.session['must_change_password'] = False
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
