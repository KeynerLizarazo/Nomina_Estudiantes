from django import forms
from .models import Courses, Levels, Person, TodoItem, User

class CourseForm(forms.ModelForm):
    class Meta:
        model = Courses
        fields = ['course_name', 'image_course', 'tutor']
        widgets = {
            'course_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Del Curso'}),
            'image_course': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'tutor': forms.Select(attrs={'class': 'form-control'}),
        }

class LevelForm(forms.ModelForm):
    class Meta:
        model = Levels
        fields = ['level_name', 'description', 'duration']
        widgets = {
            'level_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del Nivel'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Descripción del Nivel'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duración en horas', 'min': '1'}),
        }

class TodoItemForm(forms.ModelForm):
    class Meta:
        model = TodoItem
        fields = ['task', 'due_date']
        widgets = {
            'task': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nueva tarea'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'documento', 'role', 'person']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de Usuario'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo Electrónico'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Documento'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'person': forms.Select(attrs={'class': 'form-control'}),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'documento', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de Usuario'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo Electrónico'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Documento'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }


class PersonForm(forms.ModelForm):
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
            'nationality'
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
            'nationality': 'Nacionalidad',
        }
        widgets = {
            'type_document': forms.Select(attrs={'class': 'form-control'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba su número de documento'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba sus nombres'}),
            'surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba sus apellidos'}),
            'progenitor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba el nombre del representante'}),
            'progenitor_document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba el número de documento del representante'}),
            'telephone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escriba el número de teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Escriba su Correo Electrónico'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.Select(attrs={'class': 'form-control'}),
        }
