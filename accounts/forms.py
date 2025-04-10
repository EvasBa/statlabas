from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django import forms
from django.utils.translation import gettext_lazy as _

CustomUser = get_user_model()

class CustomUserCreationForm(BaseUserCreationForm):
    """
    Forma naujo CustomUser kūrimui, naudojant email.
    """
    class Meta(BaseUserCreationForm.Meta):
        model = CustomUser
        # Nurodome laukus, kurie bus formoje (email, user_type ir slaptažodis yra numatyti)
        fields = ('email', 'user_type') # Pridedame user_type

    # Galima perrašyti clean() ar kitus metodus, jei reikia specifinės validacijos


class CustomUserChangeForm(BaseUserChangeForm):
    """
    Forma esamo CustomUser redagavimui.
    """
    class Meta(BaseUserChangeForm.Meta):
        model = CustomUser
        # Nurodome laukus, kurie bus rodomi redagavimo formoje
        # (atitinka jūsų admin fieldsets)
        fields = ('email', 'first_name', 'last_name', 'user_type',
                  'is_active', 'is_staff', 'is_superuser',
                  'groups', 'user_permissions')

    # Perrašome __init__, kad pašalintume username lauką, jei jis netyčia atsiranda
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Jei username vis dar yra formos laukuose, pašaliname
        if 'username' in self.fields:
            del self.fields['username']