from django.db import models
from django.contrib.auth.models import User  # Importar la clase User de autenticación


# Constante para tipos de documento
TIPO_DOCUMENTO_CHOICES = [
    ('V', 'Cédula Venezolana (V)'),
    ('CC', 'Cédula Colombiana (CC)'),
]


class Cedula(models.Model):
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


class Usuario(models.Model):
    """
    Modelo personalizado de usuario (externo a la autenticación de Django).
    NOTA: No es usado por Django Auth, sino gestionado manualmente.
    """
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    documento = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  # Para permitir hashes seguros

    class Meta:
        managed = False  # No dejar que Django administre esta tabla (probablemente está en otra base de datos)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.documento})"


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