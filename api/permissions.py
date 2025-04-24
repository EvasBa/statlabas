from rest_framework import permissions

class IsVerifiedPartnerPermission(permissions.BasePermission):
    """
    Leidžia prieigą tik autentifikuotiems vartotojams, kurie turi
    susietą ir PATVIRTINTĄ Partner (Vendor) profilį.
    """
    message = 'User is not a verified partner/vendor.' # Klaidos pranešimas

    def has_permission(self, request, view):
        # Tikrinam, ar vartotojas autentifikuotas
        if not request.user or not request.user.is_authenticated:
            return False
        # Tikrinam, ar turi susietą partnerio profilį ir ar jis patvirtintas
        # Naudojam related_name 'partner_profile' iš Partner.user lauko
        return hasattr(request.user, 'partner_profile') and request.user.partner_profile.is_verified

    # Galima implementuoti ir has_object_permission, jei reikia tikrinti
    # ar konkretus objektas (pvz., produktas) priklauso šiam partneriui,
    # bet dažnai tai daroma ViewSet'o metoduose (get_queryset, perform_update).