from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Vendor
from accounts.models import CustomUser

class VendorApplicationForm(forms.ModelForm):
    '''
    Form for user to apply to become vendor.
    '''
    terms_accepted = forms.BooleanField(
        label=_("I have read and accept the terms and conditions"),
        required=True,
        error_messages={
            'required': _("You must accept the terms and conditions to apply.")
        }
    )
    class Meta:
        model = Vendor
        fields = ['logo', 'website', 'description', 'return_policy']
        success_message = _('Your application has been submitted successfully. We will review it and get back to you soon.')
        #success_url = '/vendor/application/success/'  # URL to redirect after successful submission
        error_messages = {
            'required':_("This field is required."),
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'return_policy': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'logo': _('Logo'),
            'website': _('Website'),
            'description': _('Description'),
            'return_policy': _('Return Policy'),
        }
        help_texts = {
            'logo': _('Upload a logo for the vendor.'),
            'website': _('Vendor website URL.'),
            'description': _('Vendor description.'),
            'return_policy': _('Return policy of the vendor.'),
        }
    # dont need this as we are using the user object to get the vendor profile
    # def __init__(self, *args, **kwargs):
    #     self.user = kwargs.pop('user', None)
    #     super().__init__(*args, **kwargs)
    #     if self.user:
    #         if self.user.user_type == CustomUser.USER_TYPE_COMPANY:
    #             self.fields['description'].initial = self.user.company_profile.company_name
    #             self.fields['website'].initial = self.user.company_profile.website
    #         else:
    #             self.fields['description'].initial = f'{self.user.first_name} {self.user.last_name}'

    #     self.fields['description'].widget.attrs.update({
    #         'placeholder': _('Enter a brief description')
    #         })
    #     self.fields['website'].widget.attrs.update({
    #         'placeholder': _('Enter your website URL')
    #         })


class VendorUpdateForm(forms.ModelForm):
    '''
    Form for vendor to update their profile while maitaning their user type
    '''


    class Meta:
        model = Vendor
        fields = ['logo', 'website', 'description', 'return_policy']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'return_policy': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'logo': _('Logo'),
            'website': _('Website'),
            'description': _('Description'),
            'return_policy': _('Return Policy'),
        }

    # dont need this as we are using the user object to get the vendor profile
    # def __init__(self, *args, **kwargs):
    #     self.user = kwargs.pop('user', None)
    #     super().__init__(*args, **kwargs)
    #     if self.user:
    #         # Set initial values for common fields
    #         self.fields['first_name'].initial = self.user.first_name
    #         self.fields['last_name'].initial = self.user.last_name
    #         self.fields['email'].initial = self.user.email
    #         # Upddate user information
    #         if self.user.user_type == CustomUser.USER_TYPE_COMPANY:
    #             self.fields['company_name'].initial = forms.CharField(initial=self.user.company_profile.company_name)
    #             self.fields['company_regitration_number'].initial = forms.CharField(initial=self.user.company_profile.company_registration_number)
    #             self.fields['company_vat_number'].initial = forms.CharField(initial=self.user.company_profile.company_vat_number)
    # # Update the form fields to include company-specific fields
    # def save(self, commit=True):
    #     vendor = super().save(commit=False)
    #     if commit:
    #         self.user.first_name = self.cleaned_data['first_name']
    #         self.user.last_name = self.cleaned_data['last_name']
    #         self.user.email = self.cleaned_data['email']
    #         self.user.save()

    #         if self.user.user_type == CustomUser.USER_TYPE_COMPANY:
    #             self.user.company_profile.company_name = self.cleaned_data['company_name']
    #             self.user.company_profile.company_registration_number = self.cleaned_data['company_registration_number']
    #             self.user.company_profile.company_vat_number = self.cleaned_data['company_vat_number']
    #             self.user.company_profile.save()
    #         vendor.save()
    #     return vendor