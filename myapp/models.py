from django.db import models
from django.contrib.auth.models import User, AbstractUser, Group, Permission  # Importar la clase User de autenticación

# Constante para tipos de documento
TIPO_DOCUMENTO_CHOICES = [
    ('V', 'Cédula Venezolana (V)'),
    ('CC', 'Cédula Colombiana (CC)'),
]
GENDER_LIST_PREDIFINED = [
    ('M', 'Man'),
    ('W', 'Woman'),
]
ROLE_LIST_PREDIFINED = [
    ("student", "Student"), 
    ("tutor", "Tutor"), 
    ("admin", "Admin")
]
COURSE_MODALITY_LIST_PREDIFINED = [
    ("virtual", "Virtual"),
    ("presential", "Presential")
]

class Cedula(models.Model):
    class Meta:
        db_table = 'cedulas'
        verbose_name = 'Cédula'
        verbose_name_plural = 'Cédulas'
    """
    Modelo para almacenar registros de personas con cédulas venezolanas o colombianas.
    """
    tipo_documento = models.CharField(
        max_length=2,
        choices=TIPO_DOCUMENTO_CHOICES,
        default='V',
        verbose_name="Tipo de Documento"
    )
    numero_documento = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de Documento"
    )
    nombre = models.CharField(max_length=50, verbose_name="Nombre")
    apellido = models.CharField(max_length=50, verbose_name="Apellido")

    def __str__(self):
        return f"{self.get_tipo_documento_display()} - {self.numero_documento} - {self.nombre} {self.apellido}"


class Calendario(models.Model):
    """
    Modelo para gestionar eventos del calendario.
    """
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    fecha_inicio = models.DateTimeField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Fin")
    creador = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.titulo
    
    class Meta:
        db_table = 'calendario'
        verbose_name = 'Evento de calendario'
        verbose_name_plural = 'Eventos de calendario'


# MODELOS DE NUEVA BASE DE DATOS ACADEMIA
class Person(models.Model):
    type_document = models.CharField(max_length=2, choices=TIPO_DOCUMENTO_CHOICES, default='V')
    document_number = models.CharField(max_length=20, unique=True)
    name= models.CharField(max_length=50)
    surname= models.CharField(max_length=50)
    progenitor_name= models.CharField(max_length=50)
    progenitor_document_number= models.CharField(max_length=20, unique=True)
    telephone_number=models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_LIST_PREDIFINED, default='H')
    nationality = models.CharField(max_length=50, blank=True, null=True)
    class Meta:
        db_table = 'personas'
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        
    def __str__(self):
        return f"{self.name} ({self.document_number})"

class Students(models.Model):
    """
    Modelo que representa a un estudiante de la academia.
    Relaciona a la persona, usuario y los grupos a los que pertenece.
    """
    date_register = models.DateField()
    status = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    class Meta:
        db_table = 'estudiantes'
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'

    def __str__(self):
        return f"{self.person.name} ({self.user.username})"
    

class Grade_Students(models.Model):
    """
    Modelo que almacena las calificaciones de los estudiantes en un grupo específico.
    """
    grades = models.DecimalField(max_digits=5, decimal_places=2)
    observations = models.TextField()
    student = models.ForeignKey('Students', on_delete=models.CASCADE)
    group_level = models.ForeignKey('Group_Levels', on_delete=models.CASCADE)

    class Meta:
        db_table = 'notas_estudiantes'
        verbose_name = 'Nota de estudiante'
        verbose_name_plural = 'Notas de estudiantes'

    def __str__(self):
        return f"{self.grades} - {self.student.person.name} ({self.student.id})"

class Testing(models.Model):
    """
    Modelo que representa una evaluación aplicada a un estudiante en un grupo.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    percentage_grade = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    group_level = models.ForeignKey('Group_Levels', on_delete=models.CASCADE)

    class Meta:
        db_table = 'evaluaciones'
        verbose_name = 'Evaluación'
        verbose_name_plural = 'Evaluaciones'    

    def __str__(self):
        return f"{self.name} ({self.date}) - {self.student.person.name}"
    
class Units(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    topic_order = models.IntegerField()
    class Meta:
        db_table = 'unidades'
        verbose_name = 'Unidad'
        verbose_name_plural = 'Unidades'

    def __str__(self):
        return f"{self.name} (Tema {self.topic_order})"

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class User(AbstractUser):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    documento = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=ROLE_LIST_PREDIFINED, default='student')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True)
    groups = models.ManyToManyField(
        Group,
        related_name='usuarios_sistema_user_set',
        blank=True,
        help_text='Los grupos a los que pertenece este usuario.',
        verbose_name='grupos'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='usuarios_sistema_user_permissions_set',
        blank=True,
        help_text='Permisos específicos para este usuario.',
        verbose_name='permisos de usuario'
    )
    class Meta:
        db_table = 'usuarios_sistema'
        verbose_name = 'Usuario del sistema'
        verbose_name_plural = 'Usuarios del sistema'
    
    def __str__(self):
        return f"{self.username} ({self.role})"
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""    

class Tutors(models.Model):
    staff_position = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    class Meta:
        db_table = 'tutores'
        verbose_name = 'Tutor'
        verbose_name_plural = 'Tutores'
    
    def __str__(self):
        return f"{self.person.name} ({self.staff_position})"
class Courses(models.Model):
    course_name = models.CharField(max_length=100)
    period=models.IntegerField(help_text="Período del curso en meses")
    image_course=models.ImageField(upload_to='courses_images/', blank=True, null=True, help_text="Imagen del curso")
    tutor = models.ForeignKey(Tutors, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'cursos'
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        
    def __str__(self):
        return f"{self.course_name} ({self.study_modality})"

class Levels(models.Model):
    level_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField(help_text="Duración en horas")
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    class Meta:
        db_table = 'niveles'
        verbose_name = 'Nivel'
        verbose_name_plural = 'Niveles'

    def __str__(self):
        return f"{self.level_name} ({self.course.course_name})"
    
class Group_Levels(models.Model):
    """
    Modelo que representa un grupo de nivel en la academia.
    Un grupo puede tener muchos estudiantes y un nivel asociado.
    """
    name_group_levels = models.CharField(max_length=100)
    date_begin = models.DateField()
    date_end = models.DateField()
    study_modality = models.CharField(max_length=50, choices=COURSE_MODALITY_LIST_PREDIFINED, default='presential')
    level = models.ForeignKey('Levels', on_delete=models.CASCADE)
    students = models.ManyToManyField('Students', related_name='group_levels', blank=True)

    class Meta:
        db_table = 'grupos_niveles'
        verbose_name = 'Grupo Nivel'
        verbose_name_plural = 'Grupos Niveles'

    def __str__(self):
        return f"{self.name_group_levels} ({self.level.level_name})"