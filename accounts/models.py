from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    """Manager for CustomUser where email is the unique identifier."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    """
    Custom User model using email instead of username, with user_type.
    """
    # --- User Types ---
    USER_TYPE_PRIVATE = 'private'
    USER_TYPE_COMPANY = 'company'
    USER_TYPE_CHOICES = [
        (USER_TYPE_PRIVATE, _('Private Person')),
        (USER_TYPE_COMPANY, _('Company')),
    ]

    # --- Fields ---
    username = None # Disable username
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    user_type = models.CharField(
        _('Account Type'),
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default=USER_TYPE_PRIVATE,
        help_text=_("Indicates if the account represents an individual or a company.")
    )
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    # phone_number galima pridėti vėliau su profiliu

    # --- Manager ---
    objects = CustomUserManager()

    # --- Settings for AbstractUser ---
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # Email and password only for createsuperuser

    # --- Meta ---
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']

    # --- Properties ---
    @property
    def is_private(self):
        return self.user_type == self.USER_TYPE_PRIVATE

    @property
    def is_company(self):
        return self.user_type == self.USER_TYPE_COMPANY

    @property
    def display_name(self):
         # Paprastas variantas kol kas, vėliau naudosime CompanyProfile
         if self.get_full_name():
             return self.get_full_name()
         return self.email

    # --- Methods ---
    def __str__(self):
        # Rodo ir tipą
        return f'{self.display_name} ({self.get_user_type_display()})'

    # get_full_name ir get_short_name paveldėti iš AbstractUser veiks gerai