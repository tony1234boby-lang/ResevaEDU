# Especificaciones Técnicas: Sistema de Reservas de Espacios (Django)

## 1. Modelos (models.py)
Implementación de POO utilizando el ORM de Django.

```python
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Categoria(models.Model):
    nombre = models.CharField(max_length=100) # Teatro, Sala de reuniones, Biblioteca

    def __str__(self):
        return self.nombre

class Espacio(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    capacidad = models.IntegerField()
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    espacio = models.ForeignKey(Espacio, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def clean(self):
        # Lógica para evitar solapamiento de horarios
        solapamiento = Reserva.objects.filter(
            espacio=self.espacio,
            fecha=self.fecha
        ).filter(
            models.Q(hora_inicio__lt=self.hora_fin, hora_fin__gt=self.hora_inicio)
        ).exclude(pk=self.pk)
        
        if solapamiento.exists():
            raise ValidationError('Este espacio ya está reservado en el horario seleccionado.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
```

## 2. Vistas Principales (views.py)
Lógica de negocio para procesamiento de datos.

- `lista_espacios`: Consulta el ORM para obtener espacios y categorías.
- `crear_reserva`: Procesa el `ModelForm` de Django y aplica la lógica de validación.
- `mis_reservas`: Filtra las reservas por el usuario actual (`request.user`).
- `cancelar_reserva`: Elimina la instancia de la reserva tras validación de propiedad.

## 3. Interfaz de Usuario
Diseño basado en componentes de Django Templates ({% %}).
- Colores: Azul oscuro (#0F172A), Azul (#1E3A8A), Blanco (#FFFFFF), Dorado (#FACC15).
- Estilo: Moderno, tipo Dashboard administrativo.
