from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Partner

class PartnerApplicationForm(forms.ModelForm):
    terms_accepted = forms.BooleanField(
        label=_("I have read and accept the terms and conditions"),
        required=True,
        error_messages={
            'required': _("You must accept the terms and conditions to apply.")
        }
    )
    class Meta:
        model = Partner
        fields = ['logo', 'website', 'description', 'return_policy']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            if hasattr(self.user, 'company_profile'):
                self.fields['description'].initial = self.user.company_profile.company_name
                self.fields['website'].initial = self.user.company_profile.website

class PartnerUpdateForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = ['logo', 'website', 'description', 'return_policy']


       