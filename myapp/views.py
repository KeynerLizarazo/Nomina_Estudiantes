from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cedula
import re

def cedulas(request):
    if request.method == 'POST':
        tipo_documento = request.POST.get('tipo_documento')
        numero_documento = request.POST.get('numero_documento', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()

        # Validaciones
        if not tipo_documento or tipo_documento not in ['V', 'CC']:
            messages.error(request, 'Tipo de documento inválido.')
            return redirect('cedulas')

        if not numero_documento.isdigit() or not (6 <= len(numero_documento) <= 20):
            messages.error(request, 'Número de documento inválido.')
            return redirect('cedulas')

        # Validar longitud de nombre y apellido
        if len(nombre) > 50:
            messages.error(request, 'El nombre no puede tener más de 50 caracteres.')
            return redirect('cedulas')
        if len(apellido) > 50:
            messages.error(request, 'El apellido no puede tener más de 50 caracteres.')
            return redirect('cedulas')

        if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$", nombre):
            messages.error(request, 'Nombre inválido.')
            return redirect('cedulas')

        if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$", apellido):
            messages.error(request, 'Apellido inválido.')
            return redirect('cedulas')

        try:
            cedula_id = request.POST.get('id')
            if cedula_id:
                cedula_obj = get_object_or_404(Cedula, id=cedula_id)

                if Cedula.objects.exclude(id=cedula_id).filter(numero_documento=numero_documento).exists():
                    messages.error(request, 'El número de documento ya está registrado.')
                    return redirect('cedulas')

                # Actualizar
                cedula_obj.tipo_documento = tipo_documento
                cedula_obj.numero_documento = numero_documento
                cedula_obj.nombre = nombre
                cedula_obj.apellido = apellido
                cedula_obj.save()
                messages.success(request, 'Registro actualizado correctamente.')
            else:
                if Cedula.objects.filter(numero_documento=numero_documento).exists():
                    messages.error(request, 'El número de documento ya está registrado.')
                    return redirect('cedulas')

                # Crear nuevo
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

def eliminar_cedula(request, id):
    if request.method == 'POST':
        try:
            cedula = get_object_or_404(Cedula, id=id)
            cedula.delete()
            messages.success(request, "Registro eliminado correctamente.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al eliminar el registro: {str(e)}")
    return redirect('cedulas')

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Usuario

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
                messages.error(request, 'Contraseña incorrecta.')
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')

        return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    if 'usuario_id' in request.session:
        del request.session['usuario_id']  # Eliminar la sesión del usuario
    return redirect('login')  # Redirigir al formulario de login

from django.shortcuts import redirect

# Decorador para proteger las vistas
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