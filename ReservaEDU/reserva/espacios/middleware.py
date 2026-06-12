from django.contrib.sites.models import Site
from django.conf import settings
from allauth.socialaccount.models import SocialApp
from django.contrib.auth.models import User, Group
from espacios.models import Espacio

_db_initialized = False

def initialize_database(current_host):
    global _db_initialized
    if _db_initialized:
        return
    try:
        # 1. Configurar el Site dinámicamente con el host actual
        site, created = Site.objects.update_or_create(
            id=settings.SITE_ID,
            defaults={'domain': current_host, 'name': 'ReservaEDU'}
        )
        
        # 2. Configurar la SocialApp de Google si hay credenciales
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
        client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')
        
        if client_id and client_id not in ('', 'TU_ID_DE_CLIENTE_AQUI') and client_secret and client_secret not in ('', 'TU_SECRETO_AQUI'):
            app, app_created = SocialApp.objects.update_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': client_id,
                    'secret': client_secret,
                    'key': '',
                }
            )
            app.sites.add(site)
            
        # 3. Configurar Roles y Usuarios de Prueba si no existen
        grupo_secretaria, _ = Group.objects.get_or_create(name='Secretaría')
        
        user_sec, sec_created = User.objects.get_or_create(username='secretaria')
        if sec_created:
            user_sec.set_password('edu12345')
            user_sec.email = 'secretaria@reservaedu.edu'
            user_sec.save()
        if not user_sec.groups.filter(name='Secretaría').exists():
            user_sec.groups.add(grupo_secretaria)
            
        user_sol, sol_created = User.objects.get_or_create(username='solicitante')
        if sol_created:
            user_sol.set_password('edu12345')
            user_sol.email = 'solicitante@reservaedu.edu'
            user_sol.save()
            
        user_resp, resp_created = User.objects.get_or_create(username='responsable')
        if resp_created:
            user_resp.set_password('edu12345')
            user_resp.email = 'responsable@reservaedu.edu'
            user_resp.save()
            
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@reservaedu.edu', 'edu12345')
            
        espacios = Espacio.objects.filter(responsable__isnull=True)
        for espacio in espacios:
            espacio.responsable = user_resp
            espacio.save()
            
        _db_initialized = True
    except Exception:
        pass

class DynamicSiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_host = request.get_host()
        initialize_database(current_host)
        
        # Sincronizar dominio adicionalmente en caso de que cambie
        try:
            site = Site.objects.filter(id=settings.SITE_ID).first()
            if site and site.domain != current_host:
                site.domain = current_host
                site.save()
        except Exception:
            pass
            
        return self.get_response(request)
