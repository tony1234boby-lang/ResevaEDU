from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Espacio(models.Model):
    CATEGORIAS = [
        ('Teatro', 'Teatro'),
        ('Sala de reuniones', 'Sala de reuniones'),
        ('Biblioteca', 'Biblioteca'),
        ('Laboratorio', 'Laboratorio'),
        ('Deportivo', 'Deportivo'),
    ]

    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS)
    descripcion = models.TextField()
    capacidad = models.PositiveIntegerField()
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='espacios_responsable')

    def __str__(self):
        return f"{self.nombre} ({self.categoria})"

class Reserva(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas_solicitadas')
    espacio = models.ForeignKey(Espacio, on_delete=models.CASCADE, related_name='reservas')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    
    observaciones = models.TextField(blank=True, null=True)
    fecha_decision = models.DateTimeField(blank=True, null=True)
    decidido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas_decididas')

    def __str__(self):
        return f"Reserva de {self.usuario.username} en {self.espacio.nombre} ({self.fecha})"

    def clean(self):
        # Evitar solapamiento de horarios (solo para reservas no rechazadas)
        if self.estado != 'rechazada':
            solapamiento = Reserva.objects.filter(
                espacio=self.espacio,
                fecha=self.fecha
            ).exclude(estado='rechazada').filter(
                models.Q(hora_inicio__lt=self.hora_fin, hora_fin__gt=self.hora_inicio)
            )
            if self.pk:
                solapamiento = solapamiento.exclude(pk=self.pk)
            
            if solapamiento.exists():
                raise ValidationError('Este espacio ya está reservado o solicitado en el horario seleccionado.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class HistorialReserva(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(max_length=100) # e.g. 'creacion', 'aprobacion', 'rechazo'
    comentario = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.accion} por {self.usuario.username} en {self.fecha}"

class Notificacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificacion para {self.usuario.username}: {self.mensaje[:30]}"
