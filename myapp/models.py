from django.db import models

# Create your models here.
class Cedula(models.Model):
    cedula = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.cedula} - {self.nombre} {self.apellido}"