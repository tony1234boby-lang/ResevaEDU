# Estructura de Archivos del Proyecto Django

## 1. Modelos (models.py)
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
    imagen_url = models.URLField(blank=True)

    def __str__(self):
        return self.nombre

class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    espacio = models.ForeignKey(Espacio, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def clean(self):
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

## 2. Vistas (views.py)
```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Espacio, Reserva, Categoria
from .forms import ReservaForm # Asumiendo un ModelForm

def index(request):
    categorias = Categoria.objects.all()
    espacios = Espacio.objects.all()
    return render(request, 'index.html', {'categorias': categorias, 'espacios': espacios})

@login_required
def reservar(request, espacio_id):
    espacio = get_object_or_404(Espacio, id=espacio_id)
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.usuario = request.user
            reserva.espacio = espacio
            reserva.save()
            return redirect('mis_reservas')
    else:
        form = ReservaForm()
    return render(request, 'reservar.html', {'form': form, 'espacio': espacio})

@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(usuario=request.user)
    return render(request, 'mis_reservas.html', {'reservas': reservas})

@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    reserva.delete()
    return redirect('mis_reservas')
```

## 3. URLs (urls.py)
```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('reservar/<int:espacio_id>/', views.reservar, name='reservar'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('cancelar/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
]
```