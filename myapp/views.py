from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cedula

# Vista principal (mostrar lista de cédulas)
def cedulas(request):
    # Verificar si se está editando un registro existente
    cedula_id = request.POST.get('id')  # ID del registro a editar (si existe)
    if cedula_id:
        cedula_obj = get_object_or_404(Cedula, id=cedula_id)
    else:
        cedula_obj = None

    if request.method == 'POST':
        # Obtener los datos del formulario
        cedula_value = request.POST.get('cedula')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')

        # Validar que la cédula no esté duplicada
        if cedula_obj:
            # Si estás editando, permitir que la cédula sea la misma que ya tiene el registro
            if cedula_value != cedula_obj.cedula:  # Solo validar si la cédula cambió
                if Cedula.objects.filter(cedula=cedula_value).exists():
                    messages.error(request, "La cédula ya está registrada por otro usuario.")
                    return redirect('cedulas')
        else:
            # Si estás creando, verificar que la cédula no exista
            if Cedula.objects.filter(cedula=cedula_value).exists():
                messages.error(request, "La cédula ya está registrada.")
                return redirect('cedulas')

        # Guardar los cambios
        try:
            if cedula_obj:
                # Editar un registro existente
                cedula_obj.cedula = cedula_value
                cedula_obj.nombre = nombre
                cedula_obj.apellido = apellido
                cedula_obj.save()
                messages.success(request, "Registro actualizado correctamente.")
            else:
                # Crear un nuevo registro
                Cedula.objects.create(cedula=cedula_value, nombre=nombre, apellido=apellido)
                messages.success(request, "Registro guardado correctamente.")
        except Exception as e:
            # Capturar cualquier error inesperado
            messages.error(request, f"Ocurrió un error al guardar los cambios: {str(e)}")
            return redirect('cedulas')

        return redirect('cedulas')  # Redirigir a la página principal después de guardar

    # Si se está editando, cargar los datos del registro existente
    if request.GET.get('editar'):
        cedula_id = request.GET.get('editar')
        cedula_obj = get_object_or_404(Cedula, id=cedula_id)
    else:
        cedula_obj = None

    # Obtener todas las cédulas ingresadas
    cedulas_list = Cedula.objects.all()

    # Renderizar la plantilla con el contexto
    return render(request, 'cedulas.html', {
        'cedulas': cedulas_list,
        'cedula_obj': cedula_obj,  # Datos del registro a editar (si existe)
    })

# Vista para eliminar una cédula
def eliminar_cedula(request, id):
    cedula = get_object_or_404(Cedula, id=id)
    cedula.delete()
    messages.success(request, "Registro eliminado correctamente.")
    return redirect('cedulas')
