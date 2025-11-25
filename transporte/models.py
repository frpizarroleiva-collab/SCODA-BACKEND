from django.db import models

class Furgon(models.Model):
    patente = models.CharField(max_length=10, unique=True)
    conductor = models.CharField(max_length=120)
    activo = models.BooleanField(default=True)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patente} - {self.conductor}"
