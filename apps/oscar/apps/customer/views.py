from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.contrib.auth import login
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
# Importuojame bazinį Oscar vaizdą
from oscar.apps.customer.views import AccountRegistrationView as OscarAccountRegistrationView
from oscar.core.loading import get_class

# --- Importuojame savo formą ---
from .forms import CustomerRegistrationForm

# --- Importuojame modelius iš kitų aplikacijų ---
from accounts.models import CustomUser
from profiles.models import CompanyProfile # <<< ATKOMENTUOSIME, KAI BUS 'profiles'

# Gali prireikti Oscar krepšelio suliejimo funkcijos
Basket = get_class('basket.models', 'Basket')
BasketMiddleware = get_class('basket.middleware', 'BasketMiddleware')


# Perrašome AccountRegistrationView
class AccountRegistrationView(OscarAccountRegistrationView): # <<< PAVADINIMAS TOKS PATS KAIP OSCAR'O
    """
    Perrašytas registracijos vaizdas, naudojantis CustomRegistrationForm
    ir sukuriantis CompanyProfile, jei reikia.
    """
    form_class = CustomerRegistrationForm # Nurodome naudoti mūsų formą
    template_name = 'oscar/customer/registration.html' # Naudojame standartinį (kurį perrašysime)

    def form_valid(self, form):
        """
        Vykdoma, kai forma yra validi. Sukuria vartotoją ir CompanyProfile.
        """
        user = form.save() # Sukuria CustomUser per mūsų formos save() metodą

        # --- CompanyProfile kūrimas (reikės atkomentuoti/pridėti CompanyProfile importą) ---
        if user.is_company:
            company_data = {
                'company_name': form.cleaned_data.get('company_name'),
                'company_code': form.cleaned_data.get('company_code'),
                'company_address': form.cleaned_data.get('company_address'),
                'company_city': form.cleaned_data.get('company_city'),
                # ... (kiti company laukai iš formos) ...
                'user': user
            }
            company_data_cleaned = {k: v for k, v in company_data.items() if v is not None and v != ''}
            try:
                CompanyProfile.objects.create(**company_data_cleaned)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Nepavyko sukurti CompanyProfile vartotojui {user.email}: {e}", exc_info=True)
                messages.error(self.request, _("There was an issue setting up your company profile. Please contact support."))
        # -----------------------------------------------------------------------------

        # Priloginame vartotoją
        login(self.request, user)

        # Krepšelio suliejimas
        middleware = BasketMiddleware(lambda req: None)
        middleware.process_request(self.request)
        if hasattr(self.request, 'basket') and self.request.basket:
             self.request.basket.owner = user
             self.request.basket.save()

        return redirect(self.get_success_url()) # Nukreipiam į sėkmės puslapį