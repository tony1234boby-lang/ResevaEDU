import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reserva.settings')

import django
django.setup()

from espacios.models import Espacio

espacios_data = [
    {
        "nombre": "mini teatro",
        "categoria": "Teatro",
        "descripcion": "Espacio majestuoso de acústica impecable, ideal para eventos culturales y académicos de gran escala.",
        "capacidad": 450,
        "imagen_url": "https://images.unsplash.com/photo-1518998053901-5348d3961a04?auto=format&fit=crop&q=80&w=800"
    },
    {
        "nombre": "sala de reuniiones",
        "categoria": "Sala de reuniones",
        "descripcion": "Sala equipada con tecnología de punta para videoconferencias y juntas directivas.",
        "capacidad": 12,
        "imagen_url": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&q=80&w=800"
    },
    {
        "nombre": "Biblioteca",
        "categoria": "Biblioteca",
        "descripcion": "Un oasis de conocimiento con miles de volúmenes y estaciones de estudio silenciosas.",
        "capacidad": 80,
        "imagen_url": "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&q=80&w=800"
    },
    {
        "nombre": "labotario de Informatica",
        "categoria": "Laboratorio",
        "descripcion": "Equipado con kits de Arduino, sensores y estaciones de soldadura para proyectos técnicos.",
        "capacidad": 25,
        "imagen_url": "https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&q=80&w=800"
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
