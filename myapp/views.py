from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Cedula, Usuario, Calendario
from .forms import CalendarioForm
from django.utils import timezone
from django.db.models import Q
from functools import wraps
import json
import re


# ==============================
# Decorador personalizado para login requerido
# ==============================

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ==============================
# Funciones CRUD para Cédulas
# ==============================

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
            messages.error(request, f'Ocurrió un error: {str(e)}')
    
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
            messages.error(request, f"Ocurrió un error al eliminar el registro: {str(e)}")
    
    return redirect('cedulas')


# ==============================
# Funciones de Autenticación
# ==============================
def home(request):
    if 'usuario_id' in request.session:
        return redirect('cedulas')
    else:
        return redirect('login')
    
def login_view(request):
    """
    Gestiona el inicio de sesión del usuario.
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            usuario = Usuario.objects.get(username=username)
            if usuario.password == password:
                request.session['usuario_id'] = usuario.id
                return redirect('cedulas')
            else:
                messages.error(request, 'Credenciales incorrectas.')
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')

        return redirect('login')

    return render(request, 'login.html')


def logout_view(request):
    """
    Cierra la sesión del usuario y borra todos los datos de sesión.
    """
    request.session.flush()  # Elimina completamente la sesión
    return redirect('login')


# ==============================
# Vistas del Calendario
# ==============================

@login_required
def calendario_view(request):
    """
    Muestra el calendario con eventos registrados.
    """
    if request.method == 'POST':
        form = CalendarioForm(request.POST)
        if form.is_valid():
            calendario = form.save(commit=False)
            calendario.creador = request.user
            calendario.save()
            return redirect('calendario')
    else:
        form = CalendarioForm()
    eventos = Calendario.objects.all()
    context = {
        'form': form,
        'eventos': eventos
    }
    return render(request, 'calendario.html', context)


@csrf_exempt
def guardar_evento(request):
    """
    Guarda un evento nuevo en el calendario (AJAX).
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            evento = Calendario(
                titulo=data['titulo'],
                descripcion=data.get('descripcion'),
                fecha_inicio=data['fecha_inicio'],
                fecha_fin=data.get('fecha_fin'),
                creador=request.user if request.user.is_authenticated else None
            )
            evento.save()
            return JsonResponse({'success': True, 'id': evento.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})


@csrf_exempt
def modificar_evento(request, evento_id):
    """
    Modifica un evento existente (AJAX).
    """
    try:
        evento = Calendario.objects.get(id=evento_id)
    except Calendario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Evento no encontrado'}, status=404)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            evento.titulo = data['titulo']
            evento.descripcion = data.get('descripcion')
            evento.fecha_inicio = data['fecha_inicio']
            evento.fecha_fin = data.get('fecha_fin')
            evento.save()
            return JsonResponse({'success': True})
        except KeyError as e:
            return JsonResponse({'success': False, 'error': f'Campo faltante: {e}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@csrf_exempt
def eliminar_evento(request, evento_id):
    """
    Elimina un evento del calendario (AJAX).
    """
    if request.method == 'DELETE':
        try:
            evento = Calendario.objects.get(id=evento_id)
            evento.delete()
            return JsonResponse({'success': True})
        except Calendario.DoesNotExist:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


def eventos_json(request):
    """
    Devuelve todos los eventos en formato JSON para FullCalendar.
    """
    eventos = Calendario.objects.all()
    data = [
        {
            'id': e.id,
            'title': e.titulo,
            'start': e.fecha_inicio.isoformat(),
            'end': e.fecha_fin.isoformat() if e.fecha_fin else None,
            'description': e.descripcion
        }
        for e in eventos
    ]
    return JsonResponse(data, safe=False)