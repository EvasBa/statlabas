import logging
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth import login, get_backends
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from oscar.apps.customer.views import AccountRegistrationView as OscarAccountRegistrationView
from oscar.core.loading import get_class
from .forms import CustomerRegistrationForm

# Setup logger
logger = logging.getLogger(__name__)

# Get Oscar basket model
Basket = get_class('basket.models', 'Basket')

class AccountRegistrationView(OscarAccountRegistrationView):
    form_class = CustomerRegistrationForm
    template_name = 'oscar/customer/registration.html'
    success_url = reverse_lazy('customer:profile-view')

    def form_valid(self, form):
        """Handle registration form submission."""
        try:
            user = form.save()  # Form handles company profile creation

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
                logger.warning(
                    f"Failed to merge basket for user {user.email}: {e}",
                    exc_info=True
                )

            messages.success(
                self.request,
                _("Thanks for registering!")
            )
            return redirect(self.get_success_url())

        except Exception as e:
            logger.error(f"Registration failed: {e}", exc_info=True)
            messages.error(
                self.request,
                _("Registration failed. Please try again.")
            )
            return self.form_invalid(form)

    def get_saved_basket(self, user):
        """Get saved basket if it exists."""
        if self.request.session.get('oscar_open_basket'):
            try:
                return Basket.objects.get(
                    id=self.request.session['oscar_open_basket'],
                    status=Basket.OPEN
                )
            except Basket.DoesNotExist:
                return None
        return None