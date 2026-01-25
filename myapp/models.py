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

PAIS_ORIGEN_CHOICES = [
    ('Venezuela', 'Venezuela'),
    ('Colombia', 'Colombia'),
    ('Argentina', 'Argentina'),
    ('Bolivia', 'Bolivia'),
    ('Brasil', 'Brasil'),
    ('Chile', 'Chile'),
    ('Costa Rica', 'Costa Rica'),
    ('Cuba', 'Cuba'),
    ('República Dominicana', 'República Dominicana'),
    ('Ecuador', 'Ecuador'),
    ('El Salvador', 'El Salvador'),
    ('España', 'España'),
    ('Estados Unidos', 'Estados Unidos'),
    ('Guatemala', 'Guatemala'),
    ('Honduras', 'Honduras'),
    ('México', 'México'),
    ('Nicaragua', 'Nicaragua'),
    ('Panamá', 'Panamá'),
    ('Paraguay', 'Paraguay'),
    ('Perú', 'Perú'),
    ('Puerto Rico', 'Puerto Rico'),
    ('Uruguay', 'Uruguay'),
    ('Otro', 'Otro'),
]

class SoftDeleteManager(models.Manager):
    """
    Manager personalizado para que por defecto solo se muestren
    los registros que no están marcados como eliminados.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class TimestampedModel(models.Model):
    """
    Modelo base abstracto que agrega campos de auditoría temporal.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    
    class Meta:
        abstract = True

class SoftDeleteModel(TimestampedModel):
    """
    Modelo base abstracto con campos y métodos para la eliminación lógica.
    Incluye timestamps para auditoría completa.
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


class Calendario(TimestampedModel):
    """
    Modelo para gestionar eventos del calendario.
    Ahora con timestamps para mejor auditoría.
    """
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    fecha_inicio = models.DateTimeField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Fin")
    creador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    activo = models.BooleanField(default=True, verbose_name="Evento Activo")

    class Meta:
        db_table = 'calendario'
        verbose_name = 'Evento de calendario'
        verbose_name_plural = 'Eventos de calendario'
        # Indexes para mejor performance
        indexes = [
            models.Index(fields=['fecha_inicio', 'fecha_fin']),
            models.Index(fields=['creador', 'activo']),
            models.Index(fields=['activo', 'fecha_inicio']),
        ]
        # Ordenamiento por defecto
        ordering = ['fecha_inicio', 'titulo']

    def clean(self):
        """
        Validación personalizada para fechas.
        """
        from django.core.exceptions import ValidationError
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio >= self.fecha_fin:
            raise ValidationError('La fecha de inicio debe ser anterior a la fecha de fin.')

    def __str__(self):
        return self.titulo


# MODELOS DE NUEVA BASE DE DATOS ACADEMIA
class Person(SoftDeleteModel):
    """
    Modelo que representa una persona en el sistema.
    Mejorado con indexes y constraints para mejor performance e integridad.
    """
    type_document = models.CharField(max_length=2, choices=TIPO_DOCUMENTO_CHOICES, default='V')
    document_number = models.CharField(
        max_length=20, 
        unique=True,
        error_messages={
            'unique': 'Ya existe una persona registrada con este número de documento.'
        }
    )
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    progenitor_name = models.CharField(max_length=50, blank=True, null=True)
    progenitor_document_number = models.CharField(max_length=20, blank=True, null=True)
    telephone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True, unique=True, 
                              error_messages={
                                  'unique': 'Ya existe una persona registrada con este email.'
                              })
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_LIST_PREDIFINED, default='M')
    pais_origen = models.CharField("País de origen", max_length=50, choices=PAIS_ORIGEN_CHOICES, blank=True, null=True)
    
    class Meta:
        db_table = 'personas'
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        # Indexes para mejor performance
        indexes = [
            models.Index(fields=['document_number']),
            models.Index(fields=['email']),
            models.Index(fields=['name', 'surname']),
            models.Index(fields=['type_document', 'document_number']),
        ]
        # Ordenamiento por defecto
        ordering = ['name', 'surname']
        
    def clean(self):
        """
        Validación personalizada.
        """
        from django.core.exceptions import ValidationError
        if self.date_of_birth:
            from django.utils import timezone
            if self.date_of_birth > timezone.now().date():
                raise ValidationError('La fecha de nacimiento no puede ser futura.')
        
    def __str__(self):
        return f"{self.name} {self.surname} ({self.document_number})"

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
    

class Grade_Students(SoftDeleteModel):
    """
    Modelo que almacena las calificaciones de los estudiantes en un grupo específico.
    Conecta las notas con evaluaciones específicas.
    Ahora con SoftDelete y timestamps para mejor auditoría.
    """
    grades = models.DecimalField(max_digits=5, decimal_places=2)
    observations = models.TextField(blank=True, null=True)
    student = models.ForeignKey('Students', on_delete=models.CASCADE)
    group_level = models.ForeignKey('Group_Levels', on_delete=models.CASCADE)
    evaluacion = models.ForeignKey('Testing', on_delete=models.CASCADE, null=True, blank=True, 
                                   verbose_name='Evaluación', help_text='Evaluación asociada a esta nota')

    class Meta:
        db_table = 'notas_estudiantes'
        verbose_name = 'Nota de estudiante'
        verbose_name_plural = 'Notas de estudiantes'
        # Constraint: Un estudiante no puede tener dos notas para la misma evaluación
        unique_together = ['student', 'evaluacion']
        # Indexes para mejor performance
        indexes = [
            models.Index(fields=['student', 'evaluacion']),
            models.Index(fields=['group_level', 'created_at']),
        ]

    def __str__(self):
        evaluacion_name = self.evaluacion.name if self.evaluacion else "Sin evaluación"
        return f"{self.grades} - {self.student.person.name} - {evaluacion_name}"

class Testing(SoftDeleteModel):
    """
    Modelo que representa una evaluación aplicada a un grupo.
    Ahora con SoftDelete y timestamps para mejor auditoría.
    """
    TIPOS_EVALUACION = [
        ('examen', 'Examen'),
        ('quiz', 'Quiz'),
        ('tarea', 'Tarea'),
        ('proyecto', 'Proyecto'),
        ('participacion', 'Participación'),
        ('personalizada', 'Evaluación Personalizada'),
    ]
    
    name = models.CharField(max_length=200)  # Aumentado de 100 a 200
    description = models.TextField()
    percentage_grade = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    tipo_evaluacion = models.CharField(
        max_length=50, 
        choices=TIPOS_EVALUACION, 
        default='examen',
        verbose_name='Tipo de Evaluación'
    )
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    group_level = models.ForeignKey('Group_Levels', on_delete=models.CASCADE)

    def get_estado(self):
        """
        Calcula el estado de la evaluación basándose en:
        - Total de estudiantes del grupo
        - Notas asignadas para esta evaluación
        - Si la fecha ya pasó
        """
        from django.utils import timezone
        
        try:
            # Obtener total de estudiantes del grupo (activos)
            total_estudiantes = self.group_level.students.filter(is_deleted=False).count()
            
            # Contar cuántos estudiantes tienen nota para esta evaluación específica
            notas_asignadas = Grade_Students.objects.filter(
                evaluacion__name=self.name,
                evaluacion__group_level=self.group_level,
                grades__isnull=False
            ).count()
            
            # Verificar si la fecha ya pasó
            fecha_pasada = self.date < timezone.now().date()
            
            # Determinar el estado
            if notas_asignadas == 0:
                # No hay notas asignadas
                if fecha_pasada:
                    return 'vencida'  # La fecha pasó y no se ha calificado
                else:
                    return 'pendiente'  # Aún no llega la fecha
            elif notas_asignadas < total_estudiantes:
                # Hay algunas notas pero no todas
                return 'en_progreso'
            else:
                # Todos los estudiantes tienen nota
                return 'completada'
        except Exception as e:
            return 'pendiente'
    
    def get_estado_display(self):
        """
        Retorna el estado en formato legible.
        """
        estado = self.get_estado()
        estados = {
            'completada': 'Completada',
            'en_progreso': 'En Progreso',
            'pendiente': 'Pendiente',
            'vencida': 'Vencida'
        }
        return estados.get(estado, 'Pendiente')
    
    def get_estado_badge_class(self):
        """
        Retorna la clase CSS para el badge del estado.
        """
        estado = self.get_estado()
        clases = {
            'completada': 'bg-success',
            'en_progreso': 'bg-warning',
            'pendiente': 'bg-secondary',
            'vencida': 'bg-danger'
        }
        return clases.get(estado, 'bg-secondary')
    
    def get_progreso_calificacion(self):
        """
        Retorna el progreso de calificación (estudiantes con nota / total estudiantes del grupo)
        """
        try:
            # Contar estudiantes activos del grupo
            total_estudiantes = self.group_level.students.filter(is_deleted=False).count()
            
            # Contar cuántos estudiantes tienen nota para esta evaluación
            notas_asignadas = Grade_Students.objects.filter(
                evaluacion__name=self.name,
                evaluacion__group_level=self.group_level,
                grades__isnull=False
            ).count()
            
            return {
                'estudiantes_con_notas': notas_asignadas,
                'total_estudiantes': total_estudiantes,
                'porcentaje': round((notas_asignadas / total_estudiantes * 100), 1) if total_estudiantes > 0 else 0
            }
        except Exception as e:
            return {
                'estudiantes_con_notas': 0,
                'total_estudiantes': 0,
                'porcentaje': 0
            }

    @staticmethod
    def calcular_estado_evaluacion(nombre_evaluacion, grupo):
        """
        Método estático para calcular el estado de una evaluación específica en un grupo
        """
        from django.utils import timezone
        
        try:
            # Obtener una evaluación de referencia para la fecha
            evaluacion_ref = Testing.objects.filter(
                name=nombre_evaluacion,
                group_level=grupo
            ).first()
            
            if not evaluacion_ref:
                return 'pendiente'
            
            # Total de estudiantes activos del grupo
            total_estudiantes = grupo.students.filter(is_deleted=False).count()
            
            # Contar notas para esta evaluación
            notas_asignadas = Grade_Students.objects.filter(
                evaluacion__name=nombre_evaluacion,
                evaluacion__group_level=grupo,
                grades__isnull=False
            ).count()
            
            # Verificar si la fecha ya pasó
            fecha_pasada = evaluacion_ref.date < timezone.now().date()
            
            # Determinar el estado
            if notas_asignadas == 0:
                return 'vencida' if fecha_pasada else 'pendiente'
            elif notas_asignadas < total_estudiantes:
                return 'en_progreso'
            else:
                return 'completada'
                
        except Exception as e:
            return 'pendiente'

    class Meta:
        db_table = 'evaluaciones'
        verbose_name = 'Evaluación'
        verbose_name_plural = 'Evaluaciones'
        # Constraint: Un estudiante no puede tener dos evaluaciones con el mismo nombre en el mismo grupo
        unique_together = ['name', 'student', 'group_level']
        # Indexes para mejor performance
        indexes = [
            models.Index(fields=['group_level', 'date']),
            models.Index(fields=['tipo_evaluacion', 'date']),
            models.Index(fields=['student', 'group_level']),
            models.Index(fields=['name', 'group_level']),
        ]
        # Ordenamiento por defecto
        ordering = ['-date', 'name']

    def clean(self):
        """
        Validación personalizada.
        """
        from django.core.exceptions import ValidationError
        if self.percentage_grade < 0 or self.percentage_grade > 100:
            raise ValidationError('El porcentaje debe estar entre 0 y 100.')

    def __str__(self):
        return f"{self.name} ({self.date}) - {self.student.person.name}"
    
class Units(SoftDeleteModel):
    """
    Modelo que representa las unidades de contenido de un nivel.
    Ahora con SoftDelete y timestamps para mejor auditoría.
    """
    title = models.CharField(max_length=100)
    content = models.TextField(blank=True, null=True)
    pdf_material = models.FileField(upload_to='materials/', blank=True, null=True)
    topic_order = models.IntegerField()
    level = models.ForeignKey('Levels', on_delete=models.CASCADE, related_name='units', null=True)
    
    class Meta:
        db_table = 'unidades'
        verbose_name = 'Unidad'
        verbose_name_plural = 'Unidades'
        # Constraint: No puede haber dos unidades con el mismo orden en el mismo nivel
        unique_together = ['level', 'topic_order']
        # Indexes para mejor performance
        indexes = [
            models.Index(fields=['level', 'topic_order']),
            models.Index(fields=['title']),
        ]
        # Ordenamiento por defecto
        ordering = ['level', 'topic_order']

    def __str__(self):
        return f"{self.title} (Tema {self.topic_order})"

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class User(AbstractUser, SoftDeleteModel):
    must_change_password = models.BooleanField(default=False, verbose_name="Debe cambiar contraseña")
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

class Levels(TimestampedModel):
    """
    Modelo que representa los niveles de un curso.
    Ahora con timestamps para mejor auditoría.
    """
    level_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField(help_text="Duración en horas")
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'niveles'
        verbose_name = 'Nivel'
        verbose_name_plural = 'Niveles'
        # Constraint: No puede haber dos niveles con el mismo nombre en el mismo curso
        unique_together = ['level_name', 'course']
        # Indexes para mejor performance
        indexes = [
            models.Index(fields=['course', 'level_name']),
            models.Index(fields=['duration']),
        ]
        # Ordenamiento por defecto
        ordering = ['course', 'level_name']

    def __str__(self):
        return f"{self.level_name} ({self.course.course_name})"
    
class Group_Levels(SoftDeleteModel):
    """
    Modelo que representa un grupo de nivel en la academia.
    Un grupo puede tener muchos estudiantes y un nivel asociado.
    Ahora con SoftDelete y timestamps para mejor auditoría.
    """
    name_group_levels = models.CharField(max_length=100)
    date_begin = models.DateField()
    date_end = models.DateField()
    study_modality = models.CharField(max_length=50, choices=COURSE_MODALITY_LIST_PREDIFINED, default='presencial')
    level = models.ForeignKey('Levels', on_delete=models.CASCADE)
    students = models.ManyToManyField('Students', related_name='group_levels', blank=True)
    cohort = models.IntegerField(help_text="Cohorte del Grupo", blank=True, null=True)

    class Meta:
        db_table = 'grupos_niveles'
        verbose_name = 'Grupo Nivel'
        verbose_name_plural = 'Grupos Niveles'
        # Constraint: No puede haber dos grupos con el mismo nombre en el mismo nivel
        unique_together = ['name_group_levels', 'level']
        # Indexes para mejor performance
        indexes = [
            models.Index(fields=['level', 'date_begin']),
            models.Index(fields=['study_modality', 'cohort']),
            models.Index(fields=['date_begin', 'date_end']),
        ]
        # Ordenamiento por defecto
        ordering = ['-date_begin', 'name_group_levels']

    def clean(self):
        """
        Validación personalizada para fechas.
        """
        from django.core.exceptions import ValidationError
        if self.date_begin and self.date_end and self.date_begin >= self.date_end:
            raise ValidationError('La fecha de inicio debe ser anterior a la fecha de fin.')

    def __str__(self):
        return f"{self.name_group_levels} ({self.level.level_name})"

class TodoItem(TimestampedModel):
    """
    Modelo para las tareas del sistema To-Do.
    Ahora con timestamps para mejor auditoría.
    """
    task = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(
        max_length=20, 
        choices=[('low', 'Baja'), ('medium', 'Media'), ('high', 'Alta')], 
        default='medium', 
        verbose_name="Prioridad"
    )
    
    class Meta:
        db_table = 'tareas'
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'
        # Indexes para mejor performance
        indexes = [
            models.Index(fields=['user', 'completed']),
            models.Index(fields=['due_date', 'priority']),
            models.Index(fields=['created_at']),
        ]
        # Ordenamiento por defecto
        ordering = ['-priority', 'due_date', '-created_at']

    def __str__(self):
        return self.task
