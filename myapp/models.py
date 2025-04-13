from django.db import models

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