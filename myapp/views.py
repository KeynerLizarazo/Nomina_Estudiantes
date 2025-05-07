from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cedula, Usuario
import re

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
        contraseña = request.POST.get('contraseña', '').strip()

        try:
            # Buscar al usuario en la base de datos por nombre de usuario
            usuario = Usuario.objects.get(username=username)


            # Validar la contraseña
            if usuario.contraseña == contraseña:
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
    # Lógica de la vista...
    cedula_obj = None
    if request.GET.get('editar'):
        cedula_id = request.GET.get('editar')
        cedula_obj = get_object_or_404(Cedula, id=cedula_id)

    cedulas_list = Cedula.objects.all()

    return render(request, 'cedulas.html', {
        'cedulas': cedulas_list,
        'cedula_obj': cedula_obj,

    })
    
    # CALENDARIO VIEWS
def calendario_view(request):
    return render(request, 'calendario.html')
