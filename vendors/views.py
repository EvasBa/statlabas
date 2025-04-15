from django.shortcuts import render, redirect
from django.views.generic import CreateView, TemplateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext as _

from .forms import VendorApplicationForm, VendorUpdateForm
from .models import Vendor

class VendorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'vendor_profile')
    login_url = reverse_lazy('oscar:customer:login')  # URL to redirect if the user is not a vendor
    permission_denied_message = _("You must be a vendor to access this page.")
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.login_url)
        messages.error(self.request, self.permission_denied_message())
        return redirect(reverse_lazy('oscar:customer:profile-view'))  # Redirect to a different page if permission is denied
    
class VendorDashboardView(LoginRequiredMixin, VendorRequiredMixin, TemplateView):
    '''
    View for vendor dashboard.
    '''
    template_name = 'vendors/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.request.user.vendor_profile
        return context
    
class VendorProfileUpdateView(LoginRequiredMixin, VendorRequiredMixin, UpdateView):
    model = Vendor
    form_class = VendorUpdateForm
    template_name = 'vendors/profile_update.html'
    success_url = reverse_lazy('vendors:dashboard')  # URL to redirect after successful update
    def get_object(self, queryset=None):
        # Get the vendor profile associated with the logged-in user
        return self.request.user.vendor_profile
    # dont need this as we are using the user object to get the vendor profile
    # def get_form_kwargs(self):
    #     # Get the default form kwargs
    #     kwargs = super().get_form_kwargs()
    #     kwargs['user'] = self.request
    #     return kwargs
    def form_valid(self, form):
        messages.success(self.request, _("Your profile has been updated successfully."))
        return super().form_valid(form)


class VendorApplicationView(LoginRequiredMixin, CreateView):
    '''
    View for user to apply to become vendor.
    '''
    model = Vendor
    form_class = VendorApplicationForm
    template_name = 'vendors/application_form.html'
    success_url = reverse_lazy('vendors:application-success')  # URL to redirect after successful submission
    #
    # def get_form_kwargs(self):
    #     # Get the default form kwargs
    #     kwargs = super().get_form_kwargs()
    #     kwargs['user'] = self.request.user
    #     return kwargs

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'vendor_profile'):
            messages.info(request, _("You have already have a vendor profile."))
            if request.user.vendor_profile.is_verified:
                return redirect(reverse_lazy('vendors:dashboard'))
            else:
                return redirect(reverse_lazy('oscar:customer:profile-view'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not form.cleaned_data.get('terms_accepted'):
            form.add_error('terms_accepted', _("You must accept the terms and conditions to apply."))
            return self.form_invalid(form)
        
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.verification_status = Vendor.VERIFICATION_PENDING
        self.object.save()
        messages.success(self.request, _("Your application has been submitted successfully. We will review it and get back to you soon."))
        
        # Optionally, you can send an email notification to the user or admin here
        # send_email_notification(self.object)
        # send_notification_to_admin(self.object)
        
        
        return redirect(self.success_url)
    

class VendorApplicationSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'vendors/application_success.html'


class VendorApplicationSubmittedView(LoginRequiredMixin, TemplateView):
    template_name = 'vendors/application_submitted.html' # <<< Pakeistas kelias