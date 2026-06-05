import os
import django

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reserva.settings')
django.setup()

from django.contrib.auth.models import User, Group
from espacios.models import Espacio

def run_setup():
    print("Iniciando configuración de roles y usuarios de prueba...")
    
    # 1. Crear el grupo Secretaría
    grupo_secretaria, created = Group.objects.get_or_create(name='Secretaría')
    if created:
        print("Grupo 'Secretaría' creado.")
    else:
        print("Grupo 'Secretaría' ya existía.")
        
    # 2. Crear usuario secretaria
    user_sec, created = User.objects.get_or_create(username='secretaria')
    if created:
        user_sec.set_password('edu12345')
        user_sec.email = 'secretaria@reservaedu.edu'
        user_sec.save()
        print("Usuario 'secretaria' creado con contraseña: 'edu12345'")
    else:
        print("Usuario 'secretaria' ya existía.")
    
    # Añadir a la secretaría al grupo
    if not user_sec.groups.filter(name='Secretaría').exists():
        user_sec.groups.add(grupo_secretaria)
        print("Usuario 'secretaria' asignado al grupo 'Secretaría'.")
        
    # 3. Crear usuario solicitante
    user_sol, created = User.objects.get_or_create(username='solicitante')
    if created:
        user_sol.set_password('edu12345')
        user_sol.email = 'solicitante@reservaedu.edu'
        user_sol.save()
        print("Usuario 'solicitante' creado con contraseña: 'edu12345'")
    else:
        print("Usuario 'solicitante' ya existía.")
        
    # 4. Crear usuario responsable
    user_resp, created = User.objects.get_or_create(username='responsable')
    if created:
        user_resp.set_password('edu12345')
        user_resp.email = 'responsable@reservaedu.edu'
        user_resp.save()
        print("Usuario 'responsable' (responsable de espacios) creado con contraseña: 'edu12345'")
    else:
        print("Usuario 'responsable' ya existía.")
        
    # 5. Crear superusuario admin
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@reservaedu.edu', 'edu12345')
        print("Superusuario 'admin' creado con contraseña: 'edu12345'")
    else:
        print("Superusuario 'admin' ya existía.")
        
    # 6. Asignar responsable a todos los espacios
    espacios = Espacio.objects.all()
    for espacio in espacios:
        espacio.responsable = user_resp
        espacio.save()
    print(f"Asignado responsable '{user_resp.username}' a todos los {espacios.count()} espacios.")
    
    print("¡Configuración completada con éxito!")

if __name__ == '__main__':
    run_setup()
