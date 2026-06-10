"""
setup_google_oauth.py
=====================
Ejecuta este script UNA VEZ después de tener el GOOGLE_CLIENT_ID y 
GOOGLE_CLIENT_SECRET en el archivo .env.

Configura automáticamente en la base de datos de Django:
  1. El Site correcto (domain = reservaedu.onrender.com)
  2. La SocialApp de Google con Client ID y Secret
  3. Vincula la SocialApp al Site

Uso:
  cd ReservaEDU/reserva
  python manage.py shell < scratch/setup_google_oauth.py
"""

import os
import sys
import django

# ── Configurar Django ──────────────────────────────────────────────────────────
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reserva.settings')
django.setup()

from django.conf import settings
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# ── Leer credenciales desde settings (que las toma del .env) ──────────────────
CLIENT_ID     = getattr(settings, 'GOOGLE_CLIENT_ID', '')
CLIENT_SECRET = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')

if not CLIENT_ID or CLIENT_ID == 'TU_ID_DE_CLIENTE_AQUI':
    print("❌ ERROR: GOOGLE_CLIENT_ID no está configurado en el archivo .env")
    print("   Edita el archivo .env y pon el Client ID real de Google Cloud Console")
    sys.exit(1)

if not CLIENT_SECRET or CLIENT_SECRET == 'TU_SECRETO_AQUI':
    print("❌ ERROR: GOOGLE_CLIENT_SECRET no está configurado en el archivo .env")
    print("   Edita el archivo .env y pon el Client Secret real de Google Cloud Console")
    sys.exit(1)

# ── 1. Configurar el Site ──────────────────────────────────────────────────────
DOMAIN = 'reservaedu.onrender.com'
site, created = Site.objects.update_or_create(
    id=settings.SITE_ID,
    defaults={'domain': DOMAIN, 'name': 'ReservaEDU'}
)
print(f"✅ Site configurado: {site.domain} (id={site.id}) {'[CREADO]' if created else '[ACTUALIZADO]'}")

# ── 2. Crear/Actualizar la SocialApp de Google ─────────────────────────────────
app, created = SocialApp.objects.update_or_create(
    provider='google',
    defaults={
        'name':         'Google',
        'client_id':    CLIENT_ID,
        'secret':       CLIENT_SECRET,
        'key':          '',
    }
)
print(f"✅ SocialApp Google {'CREADA' if created else 'ACTUALIZADA'}")
print(f"   Client ID: {CLIENT_ID[:20]}...")

# ── 3. Vincular SocialApp al Site ──────────────────────────────────────────────
app.sites.add(site)
print(f"✅ SocialApp vinculada al site '{site.domain}'")

print()
print("🎉 ¡Configuración completa! El login con Google ya debería funcionar.")
print(f"   URL de callback registrada en Google Cloud Console:")
print(f"   https://{DOMAIN}/accounts/google/login/callback/")
