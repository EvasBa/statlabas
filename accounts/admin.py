from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # Importuojam BaseUserAdmin
# from django.contrib.auth.models import User # Nereikia, nes UserAdmin jau turi User
from django.utils.translation import gettext_lazy as _
from .forms import CustomUserCreationForm, CustomUserChangeForm

CustomUser = get_user_model()

# Standartinio User išregistruoti NEBEREIKIA, jei paveldim iš BaseUserAdmin

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin): # <<< GRĄŽINAME PAVELDĖJIMĄ IŠ BaseUserAdmin
    # Nurodome naudoti mūsų formas
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    # Laukeliai rodomi sąraše
    list_display = ('email', 'get_full_name', 'user_type', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_staff', 'is_active', 'groups')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_display_links = ('email',)

    # Naudojame BaseUserAdmin fieldsets ir pritaikome juos
    # (BaseUserAdmin.fieldsets jau yra apibrėžti, mes juos perrašome/papildome)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'user_type')}), # Pridėtas user_type
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Naudojame BaseUserAdmin add_fieldsets ir pritaikome juos
    # (BaseUserAdmin.add_fieldsets jau yra apibrėžti)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # Naudojame laukus iš mūsų CustomUserCreationForm
            'fields': ('email', 'user_type', 'password1', 'password2'), #'user_type',
        }),
    )

    # Nereikia perrašinėti get_form ar get_fieldsets, jei formos
    # ir fieldsets/add_fieldsets yra teisingai nurodyti. BaseUserAdmin
    # pats susitvarkys su formų parinkimu kūrimui/redagavimui.

    # Nereikia perrašyti save_model, nes BaseUserAdmin tvarko slaptažodį.

    # Reikia paveldimo get_full_name metodo rodymui sąraše
    # (Bet BaseUserAdmin jį jau turi)