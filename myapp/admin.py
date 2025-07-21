from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.
admin.site.register(Students) #Registro para estudiantes
admin.site.register(Person) #Registro para personas
admin.site.register(User) #Registro para usuarios
admin.site.register(Units) #Registro para unidades
admin.site.register(Courses) #Registro para cursos
admin.site.register(Levels) #Registro para niveles
admin.site.register(Group_Courses) #Registro para grupos de cursos

@admin.register(Students)
class PersonAdmin(admin.ModelAdmin):
    list_display= ('id', 'name', 'surname','type_document', 
                   'document_number','telephone_number','progenitor_name',
                   'progenitor_document_number','email', 'date_of_birth', 
                   'gender', 'nationality')
    search_fields= ('name', 'surname', 'document_number', 'email')
    list_editable=('email', 'telephone_number', 'date_of_birth',)
    list_per_page= 20
    exclude = ('id','document_number', 'progenitor_document_number', 'progenitor_name',)