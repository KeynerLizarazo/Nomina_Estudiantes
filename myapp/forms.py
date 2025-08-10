from django import forms
from .models import Courses, Levels, TodoItem

class CourseForm(forms.ModelForm):
    class Meta:
        model = Courses
        fields = ['course_name', 'cohort', 'image_course', 'tutor']
        widgets = {
            'course_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Del Curso'}),
            'cohort': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cohorte del Curso'}),
            'image_course': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'tutor': forms.Select(attrs={'class': 'form-control'}),
        }

class LevelForm(forms.ModelForm):
    class Meta:
        model = Levels
        fields = ['level_name', 'description', 'duration', 'course']
        widgets = {
            'level_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del Nivel'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Descripción del Nivel'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duración en horas'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
        }

class TodoItemForm(forms.ModelForm):
    class Meta:
        model = TodoItem
        fields = ['task', 'due_date']
        widgets = {
            'task': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nueva tarea'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
