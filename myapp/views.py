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
from .models import Cedula, Group_Levels, User, Calendario, Courses, Tutors, Levels, TodoItem, Person, Testing, Grade_Students
from .forms import CourseForm, LevelForm, PersonForm, TodoItemForm, UserForm, UserUpdateForm, DocenteForm, UnitForm, GroupLevelForm, EvaluacionForm
from django import forms
from .models import Person, Students, User, Units, Tutors
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, CharField, Max
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
            try:
                with transaction.atomic():
                    # Crear automáticamente el registro Person con los datos disponibles
                    person = Person.objects.create(
                        document_number=form.cleaned_data['documento'],
                        name=form.cleaned_data.get('username', ''),  # Temporal, se puede mejorar
                        surname='',  # Campo vacío por ahora
                        email=form.cleaned_data['email'],
                        # Los demás campos quedan vacíos/por defecto hasta que se mejore la interfaz
                    )
                    
                    # Crear el usuario y vincularlo con la persona
                    user = form.save(commit=False)
                    user.set_password(form.cleaned_data['password'])
                    user.person = person
                    user.save()
                    
                    messages.success(request, 'Usuario y persona creados exitosamente.')
                    return redirect('usuarios')
                    
            except Exception as e:
                messages.error(request, f'Error al crear usuario: {str(e)}')
                users = User.objects.all()
                context = {
                    'form': form,
                    'users': users
                }
                return render(request, self.template_name, context)
        else:
            # Crear mensaje de error detallado
            error_details = []
            for field_name, errors in form.errors.items():
                field_label = form.fields[field_name].label if field_name in form.fields else field_name
                for error in errors:
                    error_details.append(f"<strong>{field_label}:</strong> {error}")
            
            error_message = "<br>".join(error_details)
            messages.error(request, f"Errores en el formulario:<br>{error_message}")
            
            # También imprimir en consola para debugging
            print("=== ERRORES DEL FORMULARIO ===")
            for field_name, errors in form.errors.items():
                print(f"Campo '{field_name}': {errors}")
            print("=== FIN ERRORES ===")
            
            users = User.objects.all()
            context = {
                'form': form,
                'users': users
            }
            return render(request, self.template_name, context)

class UpdateUserView(LoginRequiredMixin, View):
    template_name = 'usuarios.html'
    login_url = 'login'

    def get(self, request, id, *args, **kwargs):
        user = get_object_or_404(User, id=id)
        form = UserUpdateForm(instance=user)
        users = User.objects.all()
        context = {
            'form': form,
            'users': users,
            'user_to_edit': user
        }
        return render(request, self.template_name, context)

    def post(self, request, id, *args, **kwargs):
        user = get_object_or_404(User, id=id)
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Actualizar usuario
                    user = form.save(commit=False)
                    password = request.POST.get('password')
                    if password:
                        user.set_password(password)
                    user.save()
                    
                    # SINCRONIZACIÓN: Actualizar también la tabla Person si existe
                    if user.person:
                        person = user.person
                        person.email = user.email  # Sincronizar email
                        person.document_number = user.documento  # Sincronizar documento
                        person.save()
                        print(f"✅ Sincronizado Person ID {person.id}: email={person.email}, documento={person.document_number}")
                    else:
                        print(f"⚠️ Usuario {user.username} no tiene Person asociado")
                    
                    messages.success(request, 'Usuario actualizado exitosamente (datos sincronizados).')
                    return redirect('usuarios')
                    
            except Exception as e:
                messages.error(request, f'Error al actualizar usuario: {str(e)}')
                print(f"❌ Error en sincronización: {e}")
        else:
            # Crear mensaje de error detallado
            error_details = []
            for field_name, errors in form.errors.items():
                field_label = form.fields[field_name].label if field_name in form.fields else field_name
                for error in errors:
                    error_details.append(f"<strong>{field_label}:</strong> {error}")
            
            error_message = "<br>".join(error_details)
            messages.error(request, f"Errores en el formulario:<br>{error_message}")
            
            users = User.objects.all()
            context = {
                'form': form,
                'users': users,
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


class NotasApiView(View):
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
class NotasView(LoginRequiredMixin, View):
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
        
    template_name = 'notas.html'
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
        

class AñadirGrupoApiView(View):
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

class AñadirGrupoView(LoginRequiredMixin, View):
    template_name = 'addgroup.html'
    login_url = 'login'

    def sync_students(self):
        """Sincronizar estudiantes con usuarios que tienen rol 'estudiante'"""
        existing_student_ids = set(Students.objects.filter(is_deleted=False).values_list('person_id', flat=True))
        student_users = User.objects.filter(role='estudiante', is_deleted=False)
        
        # Crear Students para personas que no tengan registro
        missing_persons = Person.objects.filter(
            is_deleted=False, 
            id__in=student_users.values_list('person_id', flat=True)
        ).exclude(id__in=existing_student_ids)
        
        for person in missing_persons:
            user = student_users.filter(person=person).first()
            if user:
                Students.objects.create(
                    date_register=timezone.now().date(),
                    status='activo',
                    user=user,
                    person=person
                )

    def get(self, request, level_id=None, *args, **kwargs):
        # Sincronizar estudiantes antes de mostrar
        self.sync_students()
        
        # Si viene de un nivel específico, obtenerlo
        selected_level = None
        if level_id:
            selected_level = get_object_or_404(Levels, id=level_id)
        
        # Crear formulario para el grupo
        form = GroupLevelForm()
        
        # Obtener estudiantes disponibles para búsqueda
        student_person_ids = set(Students.objects.filter(is_deleted=False).values_list('person_id', flat=True))
        student_users = set(User.objects.filter(role='estudiante', is_deleted=False).values_list('person_id', flat=True))
        ids = student_person_ids & student_users
        persons = Person.objects.filter(is_deleted=False, id__in=ids).only(
            'id', 'name', 'surname', 'document_number', 'email', 'telephone_number', 'type_document'
        )

        # Aplicar filtros de búsqueda
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
                    Q(type_document__icontains=query) |
                    Q(telephone_number__icontains=query)
                )

        # Paginación
        paginator = Paginator(persons.order_by('name', 'surname'), 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'form': form,
            'persons': page_obj,
            'query': query,
            'campo': campo,
            'selected_level': selected_level,
            'levels': Levels.objects.all() if not selected_level else None,
            'courses': Courses.objects.filter(is_deleted=False)
        }
        return render(request, self.template_name, context)

    def post(self, request, level_id=None, *args, **kwargs):
        # Obtener datos del formulario
        group_title = request.POST.get('group_title', '').strip()
        date_begin = request.POST.get('date_begin')
        date_end = request.POST.get('date_end')
        study_modality = request.POST.get('study_modality', 'presencial')
        
        # Si viene de URL con level_id, usarlo; sino, obtenerlo del formulario
        if level_id:
            selected_level_id = level_id
        else:
            selected_level_id = request.POST.get('level')
        
        cohort = request.POST.get('cohort')
        selected_students = request.POST.getlist('selected_students')

        # Validaciones básicas
        if not group_title:
            messages.error(request, 'El título del grupo es obligatorio.')
            return redirect('addgroup_level', level_id=level_id) if level_id else redirect('addgroup')

        if not selected_level_id:
            messages.error(request, 'Debe seleccionar un nivel.')
            return redirect('addgroup_level', level_id=level_id) if level_id else redirect('addgroup')

        try:
            with transaction.atomic():
                # Crear el grupo
                level = get_object_or_404(Levels, id=selected_level_id)
                group = Group_Levels.objects.create(
                    name_group_levels=group_title,
                    date_begin=date_begin or timezone.now().date(),
                    date_end=date_end or timezone.now().date(),
                    study_modality=study_modality,
                    level=level,
                    cohort=int(cohort) if cohort else None
                )

                # Agregar estudiantes seleccionados
                if selected_students:
                    # Obtener objetos Students basados en las personas seleccionadas
                    students_to_add = Students.objects.filter(
                        person_id__in=selected_students,
                        is_deleted=False
                    )
                    group.students.set(students_to_add)

                messages.success(request, f'Grupo {group_title} creado exitosamente con {len(selected_students)} estudiantes.')
                return redirect('grupos')

        except Exception as e:
            messages.error(request, f'Error al crear el grupo: {str(e)}')
            return redirect('addgroup_level', level_id=level_id) if level_id else redirect('addgroup')

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
            try:
                with transaction.atomic():
                    person = form.save()
                    
                    # SINCRONIZACIÓN: Actualizar también la tabla User si existe
                    from .models import User
                    try:
                        user = User.objects.get(person=person)
                        user.email = person.email or ''
                        user.first_name = person.name or ''
                        user.last_name = person.surname or ''
                        user.documento = person.document_number or ''  # ¡AGREGAR SINCRONIZACIÓN DE DOCUMENTO!
                        user.save()
                        print(f"✅ Sincronizado User ID {user.id}: email={user.email}, documento={user.documento}")
                    except User.DoesNotExist:
                        print(f"⚠️ Person {person.name} no tiene User asociado")
                    
                    messages.success(request, 'Estudiante actualizado exitosamente (datos sincronizados).')
                    return redirect('cedulas')
                    
            except Exception as e:
                messages.error(request, f'Error al actualizar estudiante: {str(e)}')
                print(f"❌ Error en sincronización: {e}")
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

class GrupoView(LoginRequiredMixin, View):
    template_name = 'grupos.html'
    login_url = 'login'

    def get(self, request, level_id=None, *args, **kwargs):
        # Si viene de un nivel específico, obtenerlo
        selected_level = None
        if level_id:
            selected_level = get_object_or_404(Levels, id=level_id)
        
        # Obtener grupos con relaciones
        grupos = Group_Levels.objects.select_related('level', 'level__course').prefetch_related('students').order_by('-id')
        
        # Filtrar por nivel si viene del contexto específico
        if selected_level:
            grupos = grupos.filter(level=selected_level)
        
        # Aplicar filtros de búsqueda
        query = request.GET.get('q')
        campo = request.GET.get('campo', 'todos')

        if query:
            if campo == 'name_group_levels':
                grupos = grupos.filter(name_group_levels__icontains=query)
            else:  # todos los campos
                grupos = grupos.filter(
                    Q(name_group_levels__icontains=query) |
                    Q(level__level_name__icontains=query) |
                    Q(level__course__course_name__icontains=query) |
                    Q(study_modality__icontains=query)
                )

        # Paginación
        paginator = Paginator(grupos, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'grupos': page_obj,
            'query': query,
            'campo': campo,
            'selected_level': selected_level,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # Crear grupo básico desde el modal (funcionalidad legacy)
        nombre = request.POST.get('name_group_levels', '').strip()
        
        if nombre:
            # Crear grupo con datos mínimos - requiere nivel
            try:
                # Buscar el primer nivel disponible como fallback
                first_level = Levels.objects.first()
                if not first_level:
                    messages.error(request, 'No hay niveles disponibles. Cree un nivel primero.')
                    return redirect('grupos')
                
                Group_Levels.objects.create(
                    name_group_levels=nombre,
                    date_begin=timezone.now().date(),
                    date_end=timezone.now().date() + timezone.timedelta(days=365),
                    study_modality='presencial',
                    level=first_level
                )
                messages.success(request, f'Grupo {nombre} creado exitosamente.')
                return redirect('grupos')
            except Exception as e:
                messages.error(request, f'Error al crear el grupo: {str(e)}')
        else:
            messages.error(request, 'El nombre del grupo es obligatorio.')
        
        return redirect('grupos')


class UpdateGrupoView(LoginRequiredMixin, View):
    def post(self, request, id, *args, **kwargs):
        grupo = get_object_or_404(Group_Levels, id=id)
        
        # Obtener datos del formulario
        nombre = request.POST.get('name_group_levels', '').strip()
        date_begin = request.POST.get('date_begin')
        date_end = request.POST.get('date_end')
        study_modality = request.POST.get('study_modality')
        cohort = request.POST.get('cohort')
        
        if not nombre:
            messages.error(request, 'El nombre del grupo es obligatorio.')
            return redirect('grupos')
        
        try:
            # Actualizar campos
            grupo.name_group_levels = nombre
            
            if date_begin:
                grupo.date_begin = date_begin
            if date_end:
                grupo.date_end = date_end
            if study_modality:
                grupo.study_modality = study_modality
            if cohort:
                grupo.cohort = int(cohort) if cohort else None
            
            grupo.save()
            messages.success(request, f'Grupo {nombre} actualizado exitosamente.')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar el grupo: {str(e)}')
        
        return redirect('grupos')


class DeleteGrupoView(LoginRequiredMixin, View):
    def post(self, request, id, *args, **kwargs):
        grupo = get_object_or_404(Group_Levels, id=id)
        nombre = grupo.name_group_levels
        grupo.delete()
        messages.success(request, f'Grupo {nombre} eliminado exitosamente.')
        return redirect('grupos')


class GrupoApiView(View):
    def get(self, request, id, *args, **kwargs):
        grupo = get_object_or_404(Group_Levels, id=id)
        data = {
            'id': grupo.id,
            'name_group_levels': grupo.name_group_levels,
            'date_begin': grupo.date_begin.strftime('%Y-%m-%d') if grupo.date_begin else '',
            'date_end': grupo.date_end.strftime('%Y-%m-%d') if grupo.date_end else '',
            'study_modality': grupo.study_modality,
            'level_id': grupo.level.id,
            'level_name': grupo.level.level_name,
            'course_name': grupo.level.course.course_name,
            'cohort': grupo.cohort,
            'students_count': grupo.students.count()
        }
        return JsonResponse(data)


#usar esta plantilla
class MisNotasView(LoginRequiredMixin, View):
    template_name = 'mis_notas.html'
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        
        
        
        

        
        return render(request, self.template_name)
    
class Perfil(LoginRequiredMixin, View):
    template_name = 'perfil.html'
    login_url = 'login'

    def get(self, request, *args, **kwargs):

        return render(request, self.template_name)

# INTENTO DE BACKEND DE GABO !!!!
class DocenteApiView(View):
    def get(self, request, id, *args, **kwargs):
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

class GrupoStudentsApiView(View):
    def get(self, request, id, *args, **kwargs):
        grupo = get_object_or_404(Group_Levels, id=id)
        students = grupo.students.select_related('person').filter(is_deleted=False)
        
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'person_id': student.person.id,
                'person_name': f"{student.person.name} {student.person.surname}",
                'person_document': f"{student.person.get_type_document_display()} {student.person.document_number}",
                'person_email': student.person.email or '',
                'person_phone': student.person.telephone_number or ''
            })
        
        return JsonResponse({
            'success': True,
            'students': students_data,
            'count': len(students_data)
        })


class StudentSearchApiView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()
        
        if not query or len(query) < 2:
            return JsonResponse({
                'success': False,
                'message': 'La búsqueda debe tener al menos 2 caracteres',
                'students': []
            })
        
        # Buscar estudiantes
        student_person_ids = set(Students.objects.filter(is_deleted=False).values_list('person_id', flat=True))
        student_users = set(User.objects.filter(role='estudiante', is_deleted=False).values_list('person_id', flat=True))
        ids = student_person_ids & student_users
        
        persons = Person.objects.filter(
            is_deleted=False, 
            id__in=ids
        ).filter(
            Q(name__icontains=query) |
            Q(surname__icontains=query) |
            Q(document_number__icontains=query)
        ).select_related()[:20]  # Limitar a 20 resultados
        
        students_data = []
        for person in persons:
            try:
                student = Students.objects.get(person=person, is_deleted=False)
                students_data.append({
                    'id': student.id,
                    'person_id': person.id,
                    'person_name': f"{person.name} {person.surname}",
                    'person_document': f"{person.get_type_document_display()} {person.document_number}",
                    'person_email': person.email or '',
                    'person_phone': person.telephone_number or ''
                })
            except Students.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'students': students_data,
            'count': len(students_data)
        })


class AddStudentToGroupView(LoginRequiredMixin, View):
    def post(self, request, id, *args, **kwargs):
        try:
            grupo = get_object_or_404(Group_Levels, id=id)
            data = json.loads(request.body)
            student_id = data.get('student_id')
            
            if not student_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de estudiante requerido'
                })
            
            student = get_object_or_404(Students, id=student_id, is_deleted=False)
            
            # Verificar si ya está en el grupo
            if grupo.students.filter(id=student_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'El estudiante ya está en este grupo'
                })
            
            # Agregar estudiante al grupo
            grupo.students.add(student)
            
            # Sincronizar evaluaciones: crear evaluaciones existentes para el nuevo estudiante
            evaluaciones_existentes = Testing.objects.filter(
                group_level=grupo
            ).values('name', 'description', 'date', 'percentage_grade', 'tipo_evaluacion').distinct()
            
            evaluaciones_creadas = 0
            for eval_data in evaluaciones_existentes:
                # Verificar si ya existe esta evaluación para el estudiante
                if not Testing.objects.filter(
                    name=eval_data['name'],
                    student=student,
                    group_level=grupo
                ).exists():
                    Testing.objects.create(
                        name=eval_data['name'],
                        description=eval_data['description'],
                        date=eval_data['date'],
                        percentage_grade=eval_data['percentage_grade'],
                        tipo_evaluacion=eval_data['tipo_evaluacion'],
                        student=student,
                        group_level=grupo
                    )
                    evaluaciones_creadas += 1
            
            message = f'Estudiante {student.person.name} agregado al grupo'
            if evaluaciones_creadas > 0:
                message += f' y sincronizado con {evaluaciones_creadas} evaluaciones'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'students_count': grupo.students.count(),
                'evaluaciones_sincronizadas': evaluaciones_creadas
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al agregar estudiante: {str(e)}'
            })


class RemoveStudentFromGroupView(LoginRequiredMixin, View):
    def post(self, request, id, *args, **kwargs):
        try:
            grupo = get_object_or_404(Group_Levels, id=id)
            data = json.loads(request.body)
            student_id = data.get('student_id')
            
            if not student_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de estudiante requerido'
                })
            
            student = get_object_or_404(Students, id=student_id, is_deleted=False)
            
            # Verificar si está en el grupo
            if not grupo.students.filter(id=student_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'El estudiante no está en este grupo'
                })
            
            # Remover estudiante del grupo
            grupo.students.remove(student)
            
            # Sincronizar evaluaciones: eliminar evaluaciones del estudiante en este grupo
            evaluaciones_eliminadas = Testing.objects.filter(
                student=student,
                group_level=grupo
            ).count()
            
            # Eliminar también las notas asociadas
            Grade_Students.objects.filter(
                student=student,
                group_level=grupo
            ).delete()
            
            # Eliminar las evaluaciones
            Testing.objects.filter(
                student=student,
                group_level=grupo
            ).delete()
            
            message = f'Estudiante {student.person.name} removido del grupo'
            if evaluaciones_eliminadas > 0:
                message += f' y eliminadas {evaluaciones_eliminadas} evaluaciones asociadas'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'students_count': grupo.students.count(),
                'evaluaciones_eliminadas': evaluaciones_eliminadas
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al remover estudiante: {str(e)}'
            })


class EvaluacionesListView(LoginRequiredMixin, View):
    """
    Vista para listar evaluaciones de un grupo específico.
    Incluye funcionalidades de búsqueda, filtrado y paginación.
    """
    template_name = 'evaluaciones.html'
    login_url = 'login'

    def get(self, request, group_id, *args, **kwargs):
        # Obtener el grupo específico
        group = get_object_or_404(Group_Levels, id=group_id)
        
        # Obtener todas las evaluaciones del grupo (agrupadas por nombre)
        evaluaciones_raw = Testing.objects.filter(group_level=group).select_related('student', 'student__person')
        
        # Agrupar evaluaciones por nombre para mostrar una fila por evaluación
        evaluaciones_dict = {}
        for evaluacion in evaluaciones_raw:
            if evaluacion.name not in evaluaciones_dict:
                evaluaciones_dict[evaluacion.name] = {
                    'evaluacion': evaluacion,  # Usar la primera como representante
                    'total_estudiantes': 0,
                    'estudiantes_con_notas': 0,
                    'estado': 'pendiente'
                }
            
            evaluaciones_dict[evaluacion.name]['total_estudiantes'] += 1
            
            # Verificar si tiene notas en Grade_Students
            if Grade_Students.objects.filter(evaluacion=evaluacion, grades__isnull=False).exists():
                evaluaciones_dict[evaluacion.name]['estudiantes_con_notas'] += 1
        
        # Convertir a lista para paginación
        evaluaciones_list = []
        for nombre, data in evaluaciones_dict.items():
            eval_data = data['evaluacion']
            
            # Calcular estado basado en notas (simplificado por ahora)
            total = data['total_estudiantes']
            con_notas = data['estudiantes_con_notas']
            
            if con_notas == 0:
                estado = 'pendiente'
            elif con_notas == total:
                estado = 'completada'
            else:
                estado = 'en_progreso'
            
            evaluaciones_list.append({
                'id': eval_data.id,
                'name': eval_data.name,
                'description': eval_data.description,
                'date': eval_data.date,
                'percentage_grade': eval_data.percentage_grade,
                'tipo_evaluacion': eval_data.get_tipo_evaluacion_display(),
                'tipo_evaluacion_code': eval_data.tipo_evaluacion,
                'total_estudiantes': total,
                'estudiantes_con_notas': con_notas,
                'estado': estado,
                'group_level': group
            })
        
        # Aplicar filtros de búsqueda
        query = request.GET.get('q', '').strip()
        tipo_filter = request.GET.get('tipo', '')
        estado_filter = request.GET.get('estado', '')
        
        if query:
            evaluaciones_list = [
                e for e in evaluaciones_list 
                if query.lower() in e['name'].lower() or 
                   query.lower() in e['description'].lower()
            ]
        
        if tipo_filter:
            evaluaciones_list = [
                e for e in evaluaciones_list 
                if e['tipo_evaluacion_code'] == tipo_filter
            ]
        
        if estado_filter:
            evaluaciones_list = [
                e for e in evaluaciones_list 
                if e['estado'] == estado_filter
            ]
        
        # Ordenar por fecha (más recientes primero)
        evaluaciones_list.sort(key=lambda x: x['date'], reverse=True)
        
        # Paginación
        paginator = Paginator(evaluaciones_list, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Calcular estadísticas del grupo
        total_evaluaciones = len(evaluaciones_list)
        total_porcentaje = sum(e['percentage_grade'] for e in evaluaciones_list)
        
        context = {
            'group': group,
            'evaluaciones': page_obj,
            'query': query,
            'tipo_filter': tipo_filter,
            'estado_filter': estado_filter,
            'total_evaluaciones': total_evaluaciones,
            'total_porcentaje': total_porcentaje,
            'tipos_evaluacion': Testing.TIPOS_EVALUACION,
            'estados_evaluacion': [
                ('pendiente', 'Pendiente'),
                ('en_progreso', 'En Progreso'),
                ('completada', 'Completada')
            ]
        }
        
        return render(request, self.template_name, context)


class CrearEvaluacionView(LoginRequiredMixin, View):
    """
    Vista para crear una nueva evaluación para un grupo.
    Crea automáticamente una evaluación para cada estudiante del grupo.
    """
    login_url = 'login'

    def post(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Group_Levels, id=group_id)
        form = EvaluacionForm(request.POST, group_level=group)
        
        if form.is_valid():
            # Validar título único en el grupo
            try:
                form.validate_unique_name_in_group()
            except forms.ValidationError as e:
                messages.error(request, str(e))
                return redirect('evaluaciones_grupo', group_id=group_id)
            
            try:
                with transaction.atomic():
                    # Obtener estudiantes del grupo
                    estudiantes = group.students.filter(is_deleted=False)
                    
                    if not estudiantes.exists():
                        messages.warning(request, 'No hay estudiantes en este grupo. Agregue estudiantes antes de crear evaluaciones.')
                        return redirect('evaluaciones_grupo', group_id=group_id)
                    
                    # Crear evaluación para cada estudiante
                    evaluaciones_creadas = []
                    for estudiante in estudiantes:
                        evaluacion = Testing.objects.create(
                            name=form.cleaned_data['name'],
                            description=form.cleaned_data['description'],
                            date=form.cleaned_data['date'],
                            percentage_grade=form.cleaned_data['percentage_grade'],
                            tipo_evaluacion=form.cleaned_data['tipo_evaluacion'],
                            student=estudiante,
                            group_level=group
                        )
                        evaluaciones_creadas.append(evaluacion)
                    
                    messages.success(
                        request, 
                        f'Evaluación "{form.cleaned_data["name"]}" creada exitosamente para {len(evaluaciones_creadas)} estudiantes.'
                    )
                    
            except Exception as e:
                messages.error(request, f'Error al crear la evaluación: {str(e)}')
        
        else:
            # Mostrar errores del formulario
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f'{form.fields[field].label}: {error}')
            
            if error_messages:
                messages.error(request, 'Errores en el formulario: ' + '; '.join(error_messages))
        
        return redirect('evaluaciones_grupo', group_id=group_id)


class EditarEvaluacionView(LoginRequiredMixin, View):
    """
    Vista para editar una evaluación existente.
    Actualiza todas las evaluaciones con el mismo nombre en el grupo.
    """
    login_url = 'login'

    def post(self, request, group_id, evaluacion_id, *args, **kwargs):
        group = get_object_or_404(Group_Levels, id=group_id)
        evaluacion_base = get_object_or_404(Testing, id=evaluacion_id, group_level=group)
        
        form = EvaluacionForm(request.POST, instance=evaluacion_base, group_level=group)
        
        if form.is_valid():
            # Validar título único en el grupo (excluyendo las evaluaciones actuales)
            try:
                form.validate_unique_name_in_group()
            except forms.ValidationError as e:
                messages.error(request, str(e))
                return redirect('evaluaciones_grupo', group_id=group_id)
            
            try:
                with transaction.atomic():
                    # Actualizar todas las evaluaciones con el mismo nombre en el grupo
                    evaluaciones_a_actualizar = Testing.objects.filter(
                        name=evaluacion_base.name,
                        group_level=group
                    )
                    
                    count = evaluaciones_a_actualizar.update(
                        name=form.cleaned_data['name'],
                        description=form.cleaned_data['description'],
                        date=form.cleaned_data['date'],
                        percentage_grade=form.cleaned_data['percentage_grade'],
                        tipo_evaluacion=form.cleaned_data['tipo_evaluacion']
                    )
                    
                    messages.success(
                        request, 
                        f'Evaluación "{form.cleaned_data["name"]}" actualizada exitosamente para {count} estudiantes.'
                    )
                    
            except Exception as e:
                messages.error(request, f'Error al actualizar la evaluación: {str(e)}')
        
        else:
            # Mostrar errores del formulario
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f'{form.fields[field].label}: {error}')
            
            if error_messages:
                messages.error(request, 'Errores en el formulario: ' + '; '.join(error_messages))
        
        return redirect('evaluaciones_grupo', group_id=group_id)


class EliminarEvaluacionView(LoginRequiredMixin, View):
    """
    Vista para eliminar una evaluación.
    Elimina todas las evaluaciones con el mismo nombre en el grupo.
    """
    login_url = 'login'

    def post(self, request, group_id, evaluacion_id, *args, **kwargs):
        group = get_object_or_404(Group_Levels, id=group_id)
        evaluacion_base = get_object_or_404(Testing, id=evaluacion_id, group_level=group)
        
        try:
            with transaction.atomic():
                # Eliminar todas las evaluaciones con el mismo nombre en el grupo
                evaluaciones_a_eliminar = Testing.objects.filter(
                    name=evaluacion_base.name,
                    group_level=group
                )
                
                nombre_evaluacion = evaluacion_base.name
                count = evaluaciones_a_eliminar.count()
                evaluaciones_a_eliminar.delete()
                
                messages.success(
                    request, 
                    f'Evaluación "{nombre_evaluacion}" eliminada exitosamente ({count} registros eliminados).'
                )
                
        except Exception as e:
            messages.error(request, f'Error al eliminar la evaluación: {str(e)}')
        
        return redirect('evaluaciones_grupo', group_id=group_id)


class EvaluacionApiView(LoginRequiredMixin, View):
    """API para obtener datos de una evaluación específica"""
    login_url = 'login'

    def get(self, request, group_id, evaluacion_id, *args, **kwargs):
        try:
            group = get_object_or_404(Group_Levels, id=group_id)
            evaluacion = get_object_or_404(Testing, id=evaluacion_id, group_level=group)
            
            fecha_str = ''
            if evaluacion.date:
                fecha_str = evaluacion.date.strftime('%Y-%m-%d')
            
            porcentaje_str = '0'
            if evaluacion.percentage_grade:
                porcentaje_str = str(evaluacion.percentage_grade)
            
            data = {
                'id': evaluacion.id,
                'name': evaluacion.name or '',
                'description': evaluacion.description or '',
                'date': fecha_str,
                'percentage_grade': porcentaje_str,
                'tipo_evaluacion': evaluacion.tipo_evaluacion or '',
                'group_name': group.name_group_levels,
                'level_name': group.level.level_name,
                'course_name': group.level.course.course_name,
                'group_level_id': group.id,
                'students_count': group.students.filter(is_deleted=False).count()
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            return JsonResponse({
                'error': 'No se pudo cargar la información de la evaluación',
                'details': str(e)
            }, status=500)


class PorcentajeTotalApiView(View):
    """
    API para obtener el porcentaje total usado en un grupo.
    """
    def get(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Group_Levels, id=group_id)
        
        # Calcular suma de porcentajes únicos por nombre de evaluación
        evaluaciones_unicas = Testing.objects.filter(
            group_level=group
        ).values('name').annotate(
            porcentaje=Max('percentage_grade')
        )
        
        total_porcentaje = sum(eval['porcentaje'] for eval in evaluaciones_unicas)
        
        data = {
            'total': float(total_porcentaje),
            'group_id': group_id,
            'group_name': group.name_group_levels
        }
        
        return JsonResponse(data)


# ==============================
# Vistas para Evaluaciones
# ==============================

class EvaluacionesListView(LoginRequiredMixin, View):
    """Vista para listar evaluaciones de un grupo específico"""
    template_name = 'evaluaciones.html'
    login_url = 'login'

    def get(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Group_Levels, id=group_id)
        
        # Obtener evaluaciones del grupo (una por nombre/fecha para evitar duplicados)
        evaluaciones = Testing.objects.filter(
            group_level=group
        ).values(
            'id', 'name', 'description', 'date', 'percentage_grade', 'tipo_evaluacion'
        ).distinct('name', 'date').order_by('name', 'date', '-id')
        
        # Convertir a lista y agregar información adicional
        evaluaciones_list = []
        for eval_data in evaluaciones:
            # Obtener una instancia para métodos del modelo
            evaluacion = Testing.objects.filter(
                id=eval_data['id']
            ).first()
            
            if evaluacion:
                eval_data['estado'] = 'pendiente'  # Por ahora estado fijo, se puede mejorar después
                eval_data['get_tipo_evaluacion_display'] = evaluacion.get_tipo_evaluacion_display()
                evaluaciones_list.append(eval_data)

        # Aplicar filtros de búsqueda
        query = request.GET.get('q')
        campo = request.GET.get('campo', 'todos')

        if query:
            if campo == 'name':
                evaluaciones_list = [e for e in evaluaciones_list if query.lower() in e['name'].lower()]
            elif campo == 'tipo':
                evaluaciones_list = [e for e in evaluaciones_list if query.lower() in e.get('get_tipo_evaluacion_display', '').lower()]
            else:  # todos los campos
                evaluaciones_list = [e for e in evaluaciones_list if 
                    query.lower() in e['name'].lower() or 
                    query.lower() in e.get('get_tipo_evaluacion_display', '').lower()]

        # Paginación
        paginator = Paginator(evaluaciones_list, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'group': group,
            'evaluaciones': page_obj,
            'query': query,
            'campo': campo,
        }
        return render(request, self.template_name, context)


class CrearEvaluacionView(LoginRequiredMixin, View):
    """Vista para crear una nueva evaluación"""
    login_url = 'login'

    def post(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Group_Levels, id=group_id)
        
        try:
            with transaction.atomic():
                # Obtener datos del formulario
                name = request.POST.get('name', '').strip()
                description = request.POST.get('description', '').strip()
                date = request.POST.get('date')
                percentage_grade = request.POST.get('percentage_grade')
                tipo_evaluacion = request.POST.get('tipo_evaluacion')

                # Validaciones básicas
                if not name:
                    messages.error(request, 'El nombre de la evaluación es obligatorio.')
                    return redirect('evaluaciones_grupo', group_id=group_id)

                # Verificar que no exista una evaluación con el mismo nombre en el grupo
                existing_eval = Testing.objects.filter(
                    name=name,
                    group_level=group
                ).first()
                
                if existing_eval:
                    messages.error(request, f'Ya existe una evaluación con el título "{name}" en este grupo.')
                    return redirect('evaluaciones_grupo', group_id=group_id)

                # Crear UNA SOLA evaluación para el grupo (sin asignar estudiante específico)
                evaluacion = Testing.objects.create(
                    name=name,
                    description=description,
                    date=date,
                    percentage_grade=percentage_grade,
                    tipo_evaluacion=tipo_evaluacion,
                    student=None,  # No asignar estudiante específico
                    group_level=group
                )

                students_count = group.students.filter(is_deleted=False).count()
                messages.success(request, f'Evaluación "{name}" creada exitosamente para el grupo con {students_count} estudiantes.')
                return redirect('evaluaciones_grupo', group_id=group_id)

        except Exception as e:
            messages.error(request, f'Error al crear la evaluación: {str(e)}')
            return redirect('evaluaciones_grupo', group_id=group_id)


class EditarEvaluacionView(LoginRequiredMixin, View):
    """Vista para editar una evaluación existente"""
    login_url = 'login'

    def post(self, request, group_id, evaluacion_id, *args, **kwargs):
        group = get_object_or_404(Group_Levels, id=group_id)
        
        try:
            with transaction.atomic():
                # Obtener datos del formulario
                name = request.POST.get('name', '').strip()
                description = request.POST.get('description', '').strip()
                date = request.POST.get('date')
                percentage_grade = request.POST.get('percentage_grade')
                tipo_evaluacion = request.POST.get('tipo_evaluacion')

                # Validaciones básicas
                if not name:
                    messages.error(request, 'El nombre de la evaluación es obligatorio.')
                    return redirect('evaluaciones_grupo', group_id=group_id)

                # Obtener la evaluación original para comparar el nombre
                evaluacion_original = Testing.objects.filter(
                    id=evaluacion_id,
                    group_level=group
                ).first()

                if not evaluacion_original:
                    messages.error(request, 'Evaluación no encontrada.')
                    return redirect('evaluaciones_grupo', group_id=group_id)

                # Si el nombre cambió, verificar que no exista otra evaluación con el nuevo nombre
                if name != evaluacion_original.name:
                    existing_eval = Testing.objects.filter(
                        name=name,
                        group_level=group
                    ).exclude(id=evaluacion_id).first()
                    
                    if existing_eval:
                        messages.error(request, f'Ya existe otra evaluación con el título "{name}" en este grupo.')
                        return redirect('evaluaciones_grupo', group_id=group_id)

                # Actualizar todas las evaluaciones con el mismo nombre original en el grupo
                evaluaciones_actualizadas = Testing.objects.filter(
                    name=evaluacion_original.name,
                    group_level=group,
                    date=evaluacion_original.date
                ).update(
                    name=name,
                    description=description,
                    date=date,
                    percentage_grade=percentage_grade,
                    tipo_evaluacion=tipo_evaluacion
                )

                messages.success(request, f'Evaluación "{name}" actualizada exitosamente para {evaluaciones_actualizadas} estudiantes.')
                return redirect('evaluaciones_grupo', group_id=group_id)

        except Exception as e:
            messages.error(request, f'Error al actualizar la evaluación: {str(e)}')
            return redirect('evaluaciones_grupo', group_id=group_id)


class EliminarEvaluacionView(LoginRequiredMixin, View):
    """Vista para eliminar una evaluación"""
    login_url = 'login'

    def post(self, request, group_id, evaluacion_id, *args, **kwargs):
        group = get_object_or_404(Group_Levels, id=group_id)
        
        try:
            with transaction.atomic():
                # Obtener la evaluación original
                evaluacion_original = Testing.objects.filter(
                    id=evaluacion_id,
                    group_level=group
                ).first()

                if not evaluacion_original:
                    messages.error(request, 'Evaluación no encontrada.')
                    return redirect('evaluaciones_grupo', group_id=group_id)

                # Eliminar todas las evaluaciones con el mismo nombre y fecha en el grupo
                evaluaciones_eliminadas = Testing.objects.filter(
                    name=evaluacion_original.name,
                    group_level=group,
                    date=evaluacion_original.date
                ).delete()

                messages.success(request, f'Evaluación "{evaluacion_original.name}" eliminada exitosamente.')
                return redirect('evaluaciones_grupo', group_id=group_id)

        except Exception as e:
            messages.error(request, f'Error al eliminar la evaluación: {str(e)}')
            return redirect('evaluaciones_grupo', group_id=group_id)


class EvaluacionApiView(LoginRequiredMixin, View):
    """API para obtener datos de una evaluación específica"""
    login_url = 'login'

    def get(self, request, group_id, evaluacion_id, *args, **kwargs):
        group = get_object_or_404(Group_Levels, id=group_id)
        evaluacion = get_object_or_404(Testing, id=evaluacion_id, group_level=group)

        data = {
            'id': evaluacion.id,
            'name': evaluacion.name,
            'description': evaluacion.description,
            'date': evaluacion.date.strftime('%Y-%m-%d'),
            'percentage_grade': float(evaluacion.percentage_grade),
            'tipo_evaluacion': evaluacion.tipo_evaluacion,
            'group_name': group.name_group_levels,
            'level_name': group.level.level_name,
            'group_level_id': group.id,
            'students_count': group.students.filter(is_deleted=False).count(),
        }
        return JsonResponse(data)


class PorcentajeTotalApiView(LoginRequiredMixin, View):
    """API para obtener el porcentaje total de evaluaciones de un grupo"""
    login_url = 'login'

    def get(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(Group_Levels, id=group_id)
        
        # Obtener evaluaciones únicas del grupo
        evaluaciones = Testing.objects.filter(group_level=group).values(
            'name', 'percentage_grade'
        ).distinct()
        
        total_percentage = sum(float(eval_data['percentage_grade']) for eval_data in evaluaciones)
        
        data = {
            'total_percentage': total_percentage,
            'remaining_percentage': max(0, 100 - total_percentage),
            'evaluaciones_count': len(evaluaciones)
        }
        return JsonResponse(data)


class GrupoApiView(LoginRequiredMixin, View):
    """API para obtener información de un grupo"""
    login_url = 'login'

    def get(self, request, id, *args, **kwargs):
        group = get_object_or_404(Group_Levels, id=id)
        
        data = {
            'id': group.id,
            'name_group_levels': group.name_group_levels,
            'level_name': group.level.level_name,
            'course_name': group.level.course.course_name,
            'students_count': group.students.filter(is_deleted=False).count(),
            'date_begin': group.date_begin.strftime('%Y-%m-%d'),
            'date_end': group.date_end.strftime('%Y-%m-%d'),
            'study_modality': group.study_modality,
        }
        return JsonResponse(data)
# ===
# ===========================
# VISTA DE PERFIL DE USUARIO
# ==============================

@login_required
def perfil_view(request):
    """
    Vista para mostrar y editar el perfil del usuario (solo correo y contraseña)
    """
    user = request.user
    
    if request.method == 'POST':
        # Obtener datos del formulario
        email = request.POST.get('email', '').strip()
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        try:
            with transaction.atomic():
                # Actualizar email si se proporcionó
                if email and email != user.email:
                    user.email = email
                    user.save()
                    
                    # También actualizar en la tabla Person si existe
                    if user.person:
                        user.person.email = email
                        user.person.save()
                
                # Cambiar contraseña si se proporcionó
                if current_password and new_password:
                    # Verificar contraseña actual
                    if not user.check_password(current_password):
                        messages.error(request, 'La contraseña actual es incorrecta.')
                        return redirect('perfil')
                    
                    # Verificar que las nuevas contraseñas coincidan
                    if new_password != confirm_password:
                        messages.error(request, 'Las nuevas contraseñas no coinciden.')
                        return redirect('perfil')
                    
                    # Verificar longitud mínima
                    if len(new_password) < 8:
                        messages.error(request, 'La nueva contraseña debe tener al menos 8 caracteres.')
                        return redirect('perfil')
                    
                    # Cambiar contraseña
                    user.set_password(new_password)
                    user.save()
                    
                    # Mantener sesión activa
                    update_session_auth_hash(request, user)
                
                messages.success(request, 'Perfil actualizado exitosamente.')
                
        except Exception as e:
            messages.error(request, f'Error al actualizar el perfil: {str(e)}')
    
    # Renderizar template con datos del usuario
    context = {
        'user': user,
        'person': user.person if hasattr(user, 'person') else None
    }
    
    return render(request, 'perfil.html', context)