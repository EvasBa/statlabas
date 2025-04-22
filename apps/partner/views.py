from django.views.generic import CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import redirect
from .models import Partner
from .forms import PartnerApplicationForm, PartnerUpdateForm

class PartnerRequiredMixin(UserPassesTestMixin):


    def test_func(self):
        return hasattr(self.request.user, 'partner_profile')
    def handle_no_permission(self):
        messages.error(self.request, _("You need to be a partner to access this page."))
        return redirect('partner:apply')

    
class PartnerApplicationView(LoginRequiredMixin, CreateView):
    model = Partner
    form_class = PartnerApplicationForm
    template_name = 'partner/application_form.html'
    success_url = reverse_lazy('partner:application_success')

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'partner_profile'):
            messages.info(request, _("You already have a partner profile."))
            return redirect('partner:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        partner = form.save(commit=False)
        partner.user = self.request.user
        partner.save()
        messages.success(self.request, _("Your application has been submitted successfully. We will review it and get back to you soon."))
        return super().form_valid(form)
    
class PartnerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'partner/dashboard.html'

    def test_func(self):
        return hasattr(self.request.user, 'partner_profile')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partner'] = self.request.user.partner_profile
        return context

class PartnerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Partner
    form_class = PartnerUpdateForm
    template_name = 'partner/update_form.html'
    success_url = reverse_lazy('partner:dashboard')

    def test_func(self):
        return hasattr(self.request.user, 'partner_profile')

    def get_object(self, queryset=None):
        return self.request.user.partner_profile

    def form_valid(self, form):
        messages.success(self.request, _("Your profile has been updated successfully."))
        return super().form_valid(form)
    
class PartnerApplicationSuccessView(LoginRequiredMixin, TemplateView):
    """Success page after partner application"""
    template_name = 'oscar/partner/application_success.html'