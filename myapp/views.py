from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Cedula

# Vista principal (mostrar lista de cédulas)
from django.shortcuts import render, redirect
from django.contrib import messages  # Para mostrar mensajes al usuario
from .models import Cedula

def cedulas(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        cedula_id = request.POST.get('id')  # Verifica si se proporciona un ID (para edición)
        cedula_value = request.POST.get('cedula')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')

        if cedula_id:
            # Editar un registro existente
            cedula_obj = Cedula.objects.get(id=cedula_id)
            cedula_obj.cedula = cedula_value
            cedula_obj.nombre = nombre
            cedula_obj.apellido = apellido
            cedula_obj.save()
        else:
            # Crear un nuevo registro
            if Cedula.objects.filter(cedula=cedula_value).exists():
                # Mostrar un mensaje de error si la cédula ya existe
                messages.error(request, "La cédula ya está registrada.")
            else:
                Cedula.objects.create(cedula=cedula_value, nombre=nombre, apellido=apellido)

        return redirect('cedulas')  # Redirige a la misma página para actualizar la lista

    # Obtener todas las cédulas ingresadas
    cedulas_list = Cedula.objects.all()
    return render(request, 'cedulas.html', {'cedulas': cedulas_list})

def editar_cedula(request, id):
    cedula = get_object_or_404(Cedula, id=id)
    if request.method == 'POST':
        # Procesar el formulario enviado
        cedula.cedula = request.POST.get('cedula')
        cedula.nombre = request.POST.get('nombre')
        cedula.apellido = request.POST.get('apellido')
        cedula.save()
        return redirect('cedulas')

    # Pasar los datos del registro existente al formulario
    return render(request, 'cedulas.html', {
        'cedula_id': cedula.id,
        'cedula_value': cedula.cedula,
        'nombre': cedula.nombre,
        'apellido': cedula.apellido,
        'cedulas': Cedula.objects.all(),  # Mantener la lista de cédulas
    })
# Vista para eliminar una cédula
def eliminar_cedula(request, id):
    cedula = get_object_or_404(Cedula, id=id)
    cedula.delete()
    return redirect('cedulas')

# Vista de prueba "Hello World"
def helloworld(request):
    return HttpResponse("Hello World bitch")