import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reserva.settings')

import django
django.setup()

from espacios.models import Espacio

# Eliminar espacios antiguos o eliminados si existen
Espacio.objects.filter(nombre__in=["sala de reuniiones", "labotario de Informatica", "mini teatro", "Coliseo Deportivo", "Laboratorio de Informática", "coliseo deportivo"]).delete()

espacios_data = [
    {
        "nombre": "Mini Teatro",
        "categoria": "Teatro",
        "descripcion": "Espacio majestuoso de acústica impecable, ideal para eventos culturales y académicos de gran escala.",
        "capacidad": 200,
        "imagen_url": "/static/images/mini_teatro.jpg"
    },
    {
        "nombre": "Sala de Reuniones",
        "categoria": "Sala de reuniones",
        "descripcion": "Sala equipada con tecnología de punta para videoconferencias y juntas directivas.",
        "capacidad": 20,
        "imagen_url": "/static/images/sala_reuniones.jpg"
    },
    {
        "nombre": "Biblioteca",
        "categoria": "Biblioteca",
        "descripcion": "Un oasis de conocimiento con miles de volúmenes y estaciones de estudio silenciosas.",
        "capacidad": 80,
        "imagen_url": "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&q=80&w=800"
    },
    {
        "nombre": "Laboratorio de Informática 1",
        "categoria": "Laboratorio",
        "descripcion": "Equipado con kits de Arduino, sensores y estaciones de soldadura para proyectos técnicos.",
        "capacidad": 20,
        "imagen_url": "/static/images/laboratorio_informatica.png"
    },
    {
        "nombre": "Laboratorio de Informática 2",
        "categoria": "Laboratorio",
        "descripcion": "Equipado con kits de Arduino, sensores y estaciones de soldadura para proyectos técnicos.",
        "capacidad": 20,
        "imagen_url": "/static/images/laboratorio_informatica.png"
    },
    {
        "nombre": "Laboratorio de Informática 3",
        "categoria": "Laboratorio",
        "descripcion": "Equipado con kits de Arduino, sensores y estaciones de soldadura para proyectos técnicos.",
        "capacidad": 20,
        "imagen_url": "/static/images/laboratorio_informatica.png"
    }
]

for data in espacios_data:
    obj, created = Espacio.objects.update_or_create(
        nombre=data["nombre"],
        defaults=data
    )
    status = "Creado" if created else "Actualizado"
    print(f"{status}: {obj.nombre} — {obj.imagen_url[:40]}...")

print("¡Listo!")
