from django.db import models
from django.contrib.auth.models import User  # Importar la clase User

class Cedula(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('V', 'Cédula Venezolana (V)'),
        ('CC', 'Cédula Colombiana (CC)'),
    ]

    tipo_documento = models.CharField(
        max_length=2,
        choices=TIPO_DOCUMENTO_CHOICES,
        default='V'
    )
    numero_documento = models.CharField(max_length=20)
    nombre = models.CharField(max_length=50)  # Límite de 50 caracteres
    apellido = models.CharField(max_length=50)  # Límite de 50 caracteres

    def __str__(self):
        return f"{self.get_tipo_documento_display()} - {self.numero_documento} - {self.nombre} {self.apellido}"

class Usuario(models.Model):
    id = models.AutoField(primary_key=True)  # Campo ID numérico autoincremental
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    documento = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)  # Campo añadido
    password = models.CharField(max_length=128) # Cambia a 128 para admitir contraseñas cifradas más largas
    
    class Meta:
        managed = False  # Indica que Django no debe gestionar esta tabla automáticamente

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.documento})"
    
class Calendario(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    creador = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.titulo