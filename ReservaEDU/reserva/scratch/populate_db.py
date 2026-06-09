import os
import django

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reserva.settings')
django.setup()

from espacios.models import Espacio

def populate():
    # Eliminar espacios antiguos con errores ortográficos si existen
    Espacio.objects.filter(nombre__in=["sala de reuniiones", "labotario de Informatica", "mini teatro"]).delete()

    espacios_data = [
        {
            "nombre": "Mini Teatro",
            "categoria": "Teatro",
            "descripcion": "Espacio majestuoso de acústica impecable, ideal para eventos culturales y académicos de gran escala.",
            "capacidad": 450,
            "imagen_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuCPX8ytcOeNLDqht-x2jWKMtnldPCDQ5iAr4zpay9oAJGRHvafkD4IX8YVVInSmMdhvdtBavFY_KXpRtNDkJyp_ZvRYS2XI_B3g3NwgkSxbBKzlpv4u2hc4nFF-haxzvYsuS4tHIUhj4kMn2QAhDKn3to3xVZ6Rw2Mwz_YrvfGnxci1BjUO0Z47KUAeiaQU-9znaZTqYIDX3gVZeX3jE7ojANqwWJhyRLJke9OIMtj5Kc3lbhb6OjwIck4OHax0GrAXkGROcIH_Hbcw"
        },
        {
            "nombre": "Sala de Reuniones",
            "categoria": "Sala de reuniones",
            "descripcion": "Sala equipada con tecnología de punta para videoconferencias y juntas directivas.",
            "capacidad": 12,
            "imagen_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDuHgoTSD5TH1RGwZnskaU07mWuz8zFd6sW0ggTWACtBdICPbcXfqbdtWIR7Dxm1ul2GJdpgmolyXqiBfYWk8GFVuVAt-0MRVIMPAKRrxAuFisKHRiWX3GNbloNvfXvliFOBzlDXTtFNdaXTM4YGpVbdwhJWiYl8BOHS7k-HcnDvJHj3MhdiHZy6tiluoSmfueD5HtoB_7b0L4fko2r9k1oEpuSp84_HOe-HzvftMRRCOA3Yc5WBM1uWPPtBMFQHv7W36XxHbfaOPp7"
        },
        {
            "nombre": "Biblioteca",
            "categoria": "Biblioteca",
            "descripcion": "Un oasis de conocimiento con miles de volúmenes y estaciones de estudio silenciosas.",
            "capacidad": 80,
            "imagen_url": "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&q=80&w=800"
        },
        {
            "nombre": "Laboratorio de Informática",
            "categoria": "Laboratorio",
            "descripcion": "Equipado con kits de Arduino, sensores y estaciones de soldadura para proyectos técnicos.",
            "capacidad": 25,
            "imagen_url": "https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&q=80&w=800"
        }
    ]

    for data in espacios_data:
        obj, created = Espacio.objects.get_or_create(
            nombre=data["nombre"],
            defaults=data
        )
        status = "Creado" if created else "Ya existía"
        print(f"{status}: {obj.nombre}")

if __name__ == "__main__":
    populate()
