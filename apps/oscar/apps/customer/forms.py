from django import forms
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from oscar.apps.customer.forms import EmailUserCreationForm

from accounts.models import CustomUser
from profiles.models import CompanyProfile

# Rename CustomRegistrationForm to CustomerRegistrationForm to match Oscar's naming
class CustomerRegistrationForm(EmailUserCreationForm):
    """Extended registration form with company fields."""
    
    user_type = forms.ChoiceField(
        label=_("Account Type"),
        choices=CustomUser.USER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial=CustomUser.USER_TYPE_PRIVATE,
        required=True,
    )

    first_name = forms.CharField(label=_("First Name"), max_length=150, required=False)
    
    last_name = forms.CharField(label=_("Last Name"), max_length=150, required=False)
    company_name = forms.CharField(label=_("Company Name"), max_length=255, required=False)
    company_registration_number = forms.CharField(label=_("Company Code"), max_length=255, required=False)
    company_vat_number = forms.CharField(label=_("Company VAT Number"), max_length=255, required=False)
    legal_address = forms.CharField(label=_("Company Address"), max_length=255, required=False)
    legal_city = forms.CharField(label=_("Company City"), max_length=255, required=False)
    legal_zip_code = forms.CharField(label=_("Company Zip Code"), max_length=20, required=False)
    legal_country = forms.CharField(label=_("Company Country"), max_length=255, required=False)
    

    class Meta:
        model = CustomUser
        fields = ('email', 'user_type', 'first_name', 'last_name')

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = self.cleaned_data["user_type"]
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        
        if commit:
            user.save()
        
        return user

# Import all other forms from oscar at the end
from apps.oscar.apps.customer.forms import *  # noqa isort:skip