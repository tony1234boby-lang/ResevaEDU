from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label=_("Nombre de usuario"),
        max_length=150,
        help_text=_("Requerido. 150 caracteres o menos. Letras, números y espacios son permitidos."),
        validators=[
            RegexValidator(
                r'^[\w\s.@+-]+$',
                _("Ingrese un nombre de usuario válido. Este valor puede contener letras, números, espacios y los caracteres @/./+/-/_."),
                'invalid'
            ),
        ],
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)
