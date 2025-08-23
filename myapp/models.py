from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, Group, Permission  # Importar la clase User de autenticación

# --- Lógica para Soft Delete (Eliminación Lógica) ---

# Constante para tipos de documento
TIPO_DOCUMENTO_CHOICES = [
    ('V', 'Cédula Venezolana (V)'),
    ('CC', 'Cédula Colombiana (CC)'),
]
GENDER_LIST_PREDIFINED = [
    ('M', 'Masculino'),
    ('F', 'Femenino'),
]
ROLE_LIST_PREDIFINED = [
    ("estudiante", "Estudiante"), 
    ("profesor", "Profesor"),
    ("tutor", "Tutor"), 
    ("admin", "Administrador")
]
COURSE_MODALITY_LIST_PREDIFINED = [
    ("virtual", "Virtual"),
    ("presencial", "Presencial")
]
STAFF_POSITION_LIST_PREDIFINED = [
    ("profesor", "Profesor"),
    ("tutor", "Tutor"),
    ("administrador", "Administrador"),
]

NATIONALITY_CHOICES = [
    ('Venezolana', 'Venezolana'),
    ('Colombiana', 'Colombiana'),
    ('Argentina', 'Argentina'),
    ('Boliviana', 'Boliviana'),
    ('Brasileña', 'Brasileña'),
    ('Chilena', 'Chilena'),
    ('Costarricense', 'Costarricense'),
    ('Cubana', 'Cubana'),
    ('Dominicana', 'Dominicana'),
    ('Ecuatoriana', 'Ecuatoriana'),
    ('Salvadoreña', 'Salvadoreña'),
    ('Española', 'Española'),
    ('Estadounidense', 'Estadounidense'),
    ('Guatemalteca', 'Guatemalteca'),
    ('Hondureña', 'Hondureña'),
    ('Mexicana', 'Mexicana'),
    ('Nicaragüense', 'Nicaragüense'),
    ('Panameña', 'Panameña'),
    ('Paraguaya', 'Paraguaya'),
    ('Peruana', 'Peruana'),
    ('Puertorriqueña', 'Puertorriqueña'),
    ('Uruguaya', 'Uruguaya'),
    ('Otra', 'Otra'),
]

class SoftDeleteManager(models.Manager):
    """
    Manager personalizado para que por defecto solo se muestren
    los registros que no están marcados como eliminados.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class SoftDeleteModel(models.Model):
    """
    Modelo base abstracto con campos y métodos para la eliminación lógica.
    """
    is_deleted = models.BooleanField(default=False, verbose_name="Eliminado")
    deleted_at = models.DateTimeField(null=True, blank=True, default=None, verbose_name="Fecha de eliminación")

    # Managers
    objects = SoftDeleteManager()  # Manager que filtra los eliminados
    all_objects = models.Manager() # Manager que devuelve todos los objetos

    def delete(self, using=None, keep_parents=False):
        """
        Sobrescribe el método delete para marcar el objeto como eliminado.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """
        Método para restaurar un objeto marcado como eliminado.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    class Meta:
        abstract = True

# --- Fin de la lógica para Soft Delete ---

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
    creador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.titulo
    
    class Meta:
        db_table = 'calendario'
        verbose_name = 'Evento de calendario'
        verbose_name_plural = 'Eventos de calendario'


# MODELOS DE NUEVA BASE DE DATOS ACADEMIA
class Person(SoftDeleteModel):
    type_document = models.CharField(max_length=2, choices=TIPO_DOCUMENTO_CHOICES, default='V')
    document_number = models.CharField(max_length=20, unique=True)
    name= models.CharField(max_length=50)
    surname= models.CharField(max_length=50)
    progenitor_name= models.CharField(max_length=50, blank=True, null=True)
    progenitor_document_number= models.CharField(max_length=20, unique=True, blank=True, null=True)
    telephone_number=models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_LIST_PREDIFINED, default='H')
    nationality = models.CharField(max_length=50, choices=NATIONALITY_CHOICES, blank=True, null=True)
    class Meta:
        db_table = 'personas'
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        
    def __str__(self):
        return f"{self.name} ({self.document_number})"

class Students(SoftDeleteModel):
    """
    Modelo que representa a un estudiante de la academia.
    Relaciona a la persona, usuario y los grupos a los que pertenece.
    """
    date_register = models.DateField()
    status = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
class User(AbstractUser, SoftDeleteModel):
    email = models.EmailField(unique=True)
    documento = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=50, choices=ROLE_LIST_PREDIFINED, default='estudiante')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True)

    REQUIRED_FIELDS = ['first_name','last_name','documento', 'role', 'email']

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

class Tutors(SoftDeleteModel):
    staff_position = models.CharField(max_length=50, choices=STAFF_POSITION_LIST_PREDIFINED, default='tutor')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    class Meta:
        db_table = 'tutores'
        verbose_name = 'Tutor'
        verbose_name_plural = 'Tutores'
    
    def __str__(self):
        return f"{self.person.name} ({self.staff_position})"
class Courses(SoftDeleteModel):
    course_name = models.CharField(max_length=100)
    image_course = models.ImageField(upload_to='courses_images/', blank=True, null=True, help_text="Imagen del curso")
    tutor = models.ForeignKey(Tutors, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        # Nota: El campo study_modality no existe en el modelo, se debe corregir o añadir.
        # Usando course_name por ahora.
        return f"{self.course_name}"

    class Meta:
        db_table = 'cursos'
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'

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
    cohort = models.IntegerField(help_text="Cohorte del Grupo", blank=True, null=True)

    class Meta:
        db_table = 'grupos_niveles'
        verbose_name = 'Grupo Nivel'
        verbose_name_plural = 'Grupos Niveles'

    def __str__(self):
        return f"{self.name_group_levels} ({self.level.level_name})"

class TodoItem(models.Model):
    task = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    due_date = models.DateField(null=True, blank=True)
    class Meta:
        db_table = 'tareas'
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'

    def __str__(self):
        return self.task
