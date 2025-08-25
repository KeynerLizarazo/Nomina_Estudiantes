from django import forms
import datetime
import re
from .models import Courses, Levels, Person, TodoItem, User, Tutors, STAFF_POSITION_LIST_PREDIFINED

class DocenteForm(forms.ModelForm):
    staff_position = forms.ChoiceField(label='Cargo', choices=STAFF_POSITION_LIST_PREDIFINED, widget=forms.Select(attrs={'class': 'form-control'}))
    document_number = forms.CharField(label='Número de Documento', max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba su número de documento'}))
    name = forms.CharField(label='Nombre', max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba sus nombres'}))
    surname = forms.CharField(label='Apellido', max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba sus apellidos'}))
    telephone_number = forms.CharField(label='Teléfono', max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba el número de teléfono'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Escriba su Correo Electrónico'}))
    date_of_birth = forms.DateField(label='Fecha de Nacimiento', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = Person
        fields = [
            'type_document',
            'document_number',
            'name',
            'surname',
            'telephone_number',
            'email',
            'date_of_birth',
            'gender',
            'pais_origen',
        ]
        labels = {
            'type_document': 'Tipo de Documento',
            'document_number': 'Numero de Documento',
            'name': 'Nombres',
            'surname': 'Apellidos',
            'telephone_number': 'Teléfono',
            'email': 'Email',
            'date_of_birth': 'Fecha de Nacimiento',
            'gender': 'Sexo',
            'pais_origen': 'País de origen',
        }
        widgets = {
            'type_document': forms.Select(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'pais_origen': forms.Select(attrs={'class': 'form-control'}),
        }

class CourseForm(forms.ModelForm):
    course_name = forms.CharField(label='Curso', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Del Curso'}))
    image_course = forms.ImageField(label='Imagen del Curso', required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}))
    tutor = forms.ModelChoiceField(queryset=Tutors.objects.all(), label='Tutor', widget=forms.Select(attrs={'class': 'form-control'}))
    class Meta:
        model = Courses
        fields = ['course_name', 'image_course', 'tutor']

class LevelForm(forms.ModelForm):
    level_name = forms.CharField(label='Nombre del Nivel', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del Nivel'}))
    description = forms.CharField(label='Descripción', max_length=500, widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Descripción del Nivel'}))
    duration = forms.IntegerField(label='Duración', min_value=1, max_value=100, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duración en horas', 'min': '1'}))
    class Meta:
        model = Levels
        fields = ['level_name', 'description', 'duration']

class TodoItemForm(forms.ModelForm):
    task = forms.CharField(label='Tarea', max_length=200, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nueva tarea'}))
    due_date = forms.DateField(label='Fecha de Vencimiento', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    class Meta:
        model = TodoItem
        fields = ['task', 'due_date']


class UserForm(forms.ModelForm):
    username = forms.CharField(label='Nombre de Usuario', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de Usuario'}))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))
    email = forms.EmailField(label='Correo Electrónico', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo Electrónico'}))
    documento = forms.CharField(label='Documento', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Documento'}))
    person = forms.ModelChoiceField(queryset=Person.objects.all(), label='Persona', widget=forms.Select(attrs={'class': 'form-control'}))
    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'documento', 'role', 'person']
        
        labels = {
            'role': 'Rol'
        }

        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'})
        }
class UserUpdateForm(forms.ModelForm):
    username = forms.CharField(label='Nombre de Usuario', max_length=150)
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    documento = forms.CharField(label='Documento', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Documento'}))
    person = forms.ModelChoiceField(queryset=Person.objects.all(), label='Persona', widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'documento', 'role', 'person']


class PersonForm(forms.ModelForm):
    document_number = forms.CharField(label='Número de Documento', max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba su número de documento'}))
    name = forms.CharField(label='Nombre', max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba sus nombres'}))
    surname = forms.CharField(label='Apellido', max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba sus apellidos'}))
    telephone_number = forms.CharField(label='Teléfono', max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba el número de teléfono'}))
    email = forms.EmailField(label='Email', required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Escriba su Correo Electrónico'}))
    date_of_birth = forms.DateField(label='Fecha de Nacimiento', required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    progenitor_document_number = forms.CharField(label='Número de Documento del Representante', max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba el número de documento del representante'}))
    progenitor_name = forms.CharField(label='Nombre del Representante', max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba el nombre del representante'}))

    class Meta:
        model = Person
        fields = [
            'type_document',
            'document_number',
            'name',
            'surname',
            'progenitor_name',
            'progenitor_document_number',
            'telephone_number',
            'email',
            'date_of_birth',
            'gender',
            'pais_origen'
        ]
        labels = {
            'type_document': 'Tipo de Documento',
            'document_number': 'Numero de Documento',
            'name': 'Nombres',
            'surname': 'Apellidos',
            'progenitor_name': 'Representante',
            'progenitor_document_number': 'Documento Representante',
            'telephone_number': 'Teléfono',
            'email': 'Email',
            'date_of_birth': 'Fecha de Nacimiento',
            'gender': 'Sexo',
            'pais_origen': 'País de origen',
        }
        widgets = {
            'type_document': forms.Select(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'pais_origen': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get('date_of_birth')
        if date_of_birth and date_of_birth > datetime.date.today():
            raise forms.ValidationError("La fecha de nacimiento no puede ser mayor al día de hoy.")
        return date_of_birth

    def clean_document_number(self):
        document_number = self.cleaned_data.get('document_number')
        if document_number and not re.match(r'^[0-9.]+$', document_number):
            raise forms.ValidationError("El número de documento solo puede contener números y puntos.")
        return document_number
