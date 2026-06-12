"""
Adaptador personalizado de allauth para ReservaEDU.
Intercepta el flujo OAuth ANTES de que allauth decida mostrar el signup form,
creando el usuario automáticamente desde los datos de Google.
"""
import re
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User


def _generate_unique_username(email):
    """Genera un username único basado en el email."""
    if email and '@' in email:
        base = re.sub(r'[^a-zA-Z0-9]', '_', email.split('@')[0])[:20]
    else:
        import time
        base = f'user_{int(time.time()) % 100000}'

    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'{base}_{counter}'
        counter += 1
    return username


class CustomAccountAdapter(DefaultAccountAdapter):
    """Adaptador de cuenta base."""

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        if not user.username:
            user.username = _generate_unique_username(user.email or '')
        if commit:
            user.save()
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adaptador que intercepta el login social ANTES de la vista de signup.
    Si el usuario de Google no existe, lo crea automáticamente en pre_social_login,
    evitando por completo la pantalla /accounts/3rdparty/signup/.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Se ejecuta después del callback de Google pero ANTES de decidir
        si mostrar el signup form. Aquí conectamos o creamos el usuario.
        """
        # Si ya tiene usuario conectado, no hacer nada
        if sociallogin.is_existing:
            return

        # Obtener email del proveedor Google
        email = sociallogin.account.extra_data.get('email', '')

        if email:
            # Buscar si ya existe un usuario con ese email
            try:
                existing_user = User.objects.get(email=email)
                # Conectar la cuenta social al usuario existente
                sociallogin.connect(request, existing_user)
                return
            except User.DoesNotExist:
                pass

        # Crear nuevo usuario automáticamente con datos de Google
        extra_data = sociallogin.account.extra_data
        first_name = extra_data.get('given_name', '')
        if not first_name and extra_data.get('name'):
            parts = extra_data['name'].split()
            first_name = parts[0] if parts else ''
        last_name = extra_data.get('family_name', '')

        username = _generate_unique_username(email)

        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        new_user.set_unusable_password()
        new_user.save()

        sociallogin.connect(request, new_user)

    def is_auto_signup_allowed(self, request, sociallogin):
        return True

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.username:
            email = data.get('email', '') or (user.email or '')
            user.username = _generate_unique_username(email)
        return user

    def save_user(self, request, sociallogin, form=None):
        user = sociallogin.user
        if not user.username:
            user.username = _generate_unique_username(user.email or '')
        return super().save_user(request, sociallogin, form)
