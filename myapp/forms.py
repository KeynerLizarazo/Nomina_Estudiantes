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
        widgets = {
            'type_document': forms.Select(attrs={'class': 'form-control'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de Documento'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
            'surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'progenitor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del Representante'}),
            'progenitor_document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de Documento del Representante'}),
            'telephone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo Electrónico'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nacionalidad'}),
        }
