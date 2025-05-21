from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Cedula, Usuario
from .models import Calendario
from .forms import CalendarioForm
from django.utils import timezone
from django.db.models import Q  # Al inicio del archivo, si no lo has hecho ya
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import re
import json
# ==============================
# Funciones CRUD para Cédulas
# ==============================

def cedulas(request):
    if request.method == 'POST':
        return guardar_cedula(request)

    # GET
    cedula_obj = None
    if request.GET.get('editar'):
        cedula_id = request.GET.get('editar')
        cedula_obj = get_object_or_404(Cedula, id=cedula_id)

    cedulas_list = Cedula.objects.all()

    return render(request, 'cedulas.html', {
        'cedulas': cedulas_list,
        'cedula_obj': cedula_obj,
    })

def guardar_cedula(request):
    if request.method == 'POST':
        cedula_id = request.POST.get('id')  # ID del registro (si existe)
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
            if cedula_id:  # Si hay un ID, estamos editando
                cedula = get_object_or_404(Cedula, id=cedula_id)
                cedula.tipo_documento = tipo_documento
                cedula.numero_documento = numero_documento
                cedula.nombre = nombre
                cedula.apellido = apellido
                cedula.save()
                messages.success(request, 'Registro actualizado correctamente.')
            else:  # Si no hay ID, estamos creando
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

def login_view(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        try:
            # Buscar al usuario en la base de datos por nombre de usuario
            usuario = Usuario.objects.get(username=username)


            # Validar la contraseña
            if usuario.password == password:
                # Guardar el ID del usuario en la sesión
                request.session['usuario_id'] = usuario.id
                return redirect('cedulas')  # Redirigir a la página principal
            else:
                messages.error(request, 'Credenciales incorrectas. Por favor, verifica tu nombre de usuario y contraseña.')
        except Usuario.DoesNotExist:
            messages.error(request, 'Credenciales incorrectas. Por favor, verifica tu nombre de usuario y contraseña.')

        return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    if 'usuario_id' in request.session:
        del request.session['usuario_id']  # Eliminar la sesión del usuario
    return redirect('login')  # Redirigir al formulario de login

# ==============================
# Decorador para Proteger Vistas
# ==============================

def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            return redirect('login')  # Redirigir al login si no hay sesión activa
        return view_func(request, *args, **kwargs)
    return wrapper

# Aplicar el decorador a la vista protegida
@login_required
def cedulas(request):
    query = request.GET.get('q', '').strip()  # Término de búsqueda
    campo = request.GET.get('campo', '').strip()  # Campo seleccionado para filtrar
    cedula_obj = None
    no_results = False  # Variable para indicar si no hay resultados
    result_count = 0  # Para contar el número de coincidencias

    if request.GET.get('editar'):
        cedula_id = request.GET.get('editar')
        cedula_obj = get_object_or_404(Cedula, id=cedula_id)

    if query:
        # Filtrar según el campo seleccionado
        if campo and campo != "todos":
            cedulas_list = Cedula.objects.filter(
                Q(**{f"{campo}__icontains": query})  # Filtrar dinámicamente por el campo seleccionado
            )
        else:
            cedulas_list = Cedula.objects.filter(
                Q(nombre__icontains=query) |
                Q(apellido__icontains=query) |
                Q(numero_documento__icontains=query) |
                Q(tipo_documento__icontains=query)
            )
        result_count = cedulas_list.count()
        if result_count == 0:  # Si no hay resultados, activamos el mensaje
            no_results = True
            cedulas_list = Cedula.objects.all()  # Mostrar todos los registros
    else:
        # Si no hay búsqueda, mostrar todas las cédulas
        cedulas_list = Cedula.objects.all()
        result_count = cedulas_list.count()

    return render(request, 'cedulas.html', {
        'cedulas': cedulas_list,
        'cedula_obj': cedula_obj,
        'query': query,
        'campo': campo,
        'no_results': no_results,
        'result_count': result_count,
    })

    # CALENDARIO VIEWS
# @login_required
def calendario_view(request):
    if request.method == 'POST':
        form = CalendarioForm(request.POST)
        if form.is_valid():
            calendario = form.save(commit=False)
            calendario.creador = request.user
            calendario.save()
            return redirect('calendario')
    else:
        form = CalendarioForm()

    eventos = Calendario.objects.all()  # Mostrar todos los eventos
    context = {
        'form': form,
        'eventos': eventos
    }
    return render(request, 'calendario.html', context)

def agregar_evento(request):
    if request.method == 'POST':
        form = CalendarioForm(request.POST)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.creador = request.user
            evento.save()
            return redirect('calendario')
    else:
        form = CalendarioForm()

    return render(request, 'calendario.html', {'form': form})

@csrf_exempt
def guardar_evento(request):
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
    try:
        # Convierte evento_id a entero
        evento_id = int(evento_id)
    except ValueError:
        return JsonResponse({'success': False, 'error': 'ID inválido'}, status=400)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Elimina la validación de creador temporalmente
            evento = Calendario.objects.get(id=evento_id)
            evento.titulo = data['titulo']
            evento.descripcion = data.get('descripcion')
            evento.fecha_inicio = data['fecha_inicio']
            evento.fecha_fin = data.get('fecha_fin')
            evento.save()
            return JsonResponse({'success': True})
        except Calendario.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Evento no encontrado'}, status=404)
        except KeyError as e:
            return JsonResponse({'success': False, 'error': f'Campo faltante: {e}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def eliminar_evento(request, evento_id):
    if request.method == 'DELETE':
        try:
            if request.user.is_authenticated:
                evento = Calendario.objects.get(id=evento_id, creador=request.user)
            else:
                evento = Calendario.objects.get(id=evento_id)
                
            evento.delete()
            return JsonResponse({'success': True})
        except Calendario.DoesNotExist:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

def eventos_json(request):
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