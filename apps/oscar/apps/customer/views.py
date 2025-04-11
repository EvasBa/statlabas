import logging
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth import login, get_backends
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from oscar.apps.customer.views import AccountRegistrationView as OscarAccountRegistrationView
from oscar.core.loading import get_class
from .forms import CustomerRegistrationForm
from accounts.models import CustomUser
from profiles.models import CompanyProfile

# Get Oscar basket model
Basket = get_class('basket.models', 'Basket')

# Setup logger
logger = logging.getLogger(__name__)

class AccountRegistrationView(OscarAccountRegistrationView):
    form_class = CustomerRegistrationForm
    template_name = 'oscar/customer/registration.html'
    success_url = reverse_lazy('customer:profile-view')

    def form_valid(self, form):
        """
        Handle valid form submission.
        """
        try:
            user = form.save()

            if user.is_company:
                company_data = {
                    'company_name': form.cleaned_data.get('company_name'),
                    'company_registration_number': form.cleaned_data.get('company_code'),
                    'company_vat_number': form.cleaned_data.get('company_vat_number'),
                    'legal_address': form.cleaned_data.get('company_address'),
                    'legal_city': form.cleaned_data.get('company_city'),
                    'legal_zip_code': form.cleaned_data.get('company_zip_code'),
                    'legal_country': form.cleaned_data.get('company_country'),
                    'user': user
                }
                company_data_cleaned = {k: v for k, v in company_data.items() if v is not None and v != ''}
                try:
                    CompanyProfile.objects.create(**company_data_cleaned)
                except Exception as e:
                    logger.error(f"Failed to create CompanyProfile for user {user.email}: {e}", exc_info=True)
                    messages.error(self.request, _("There was an issue setting up your company profile. Please contact support."))

            # Handle authentication
            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
            login(self.request, user)

            # Handle basket merging
            try:
                saved_basket = self.get_saved_basket(user)
                if saved_basket:
                    saved_basket.owner = user
                    saved_basket.save()
            except Exception as e:
                logger.warning(f"Failed to merge basket for user {user.email}: {e}", exc_info=True)

            return redirect(self.get_success_url())

        except Exception as e:
            logger.error(f"Registration failed: {e}", exc_info=True)
            messages.error(self.request, _("Registration failed. Please try again."))
            return self.form_invalid(form)

    def get_saved_basket(self, user):
        """
        Get saved basket if it exists.
        """
        if self.request.session.get('oscar_open_basket'):
            try:
                return Basket.objects.get(  # Fixed typo in 'objects'
                    id=self.request.session['oscar_open_basket'],
                    status=Basket.OPEN
                )
            except Basket.DoesNotExist:
                return None
        return None