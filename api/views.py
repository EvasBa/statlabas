from rest_framework import viewsets, status, serializers # Pridedam status ir serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from oscar.core.loading import get_model

# Importuojam mūsų leidimų klasę
from .permissions import IsVerifiedPartnerPermission
from django.core.exceptions import PermissionDenied
# Importuojam mūsų serializer'ius
from .serializers import ProductWriteSerializer, ProductReadOnlySerializer # Importuojam abu

# Importuojam modelius
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')
Partner = get_model('partner', 'Partner')

class VendorProductViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for verified vendors to manage their products.
    Allows listing, creating, retrieving, updating, and deleting products
    associated with the logged-in vendor.
    """
    # Naudosime skirtingus serializer'ius skaitymui ir rašymui
    # serializer_class = ProductWriteSerializer # Nurodysime get_serializer_class

    # Leidimai: tik prisijungęs IR patvirtintas partneris
    permission_classes = [IsAuthenticated, IsVerifiedPartnerPermission]

    def get_serializer_class(self):
        """ Grąžina skaitymo arba rašymo serializerį pagal veiksmą. """
        if self.action in ['list', 'retrieve']:
            return ProductReadOnlySerializer
        return ProductWriteSerializer # create, update, partial_update

    def get_queryset(self):
        """
        Grąžina TIK produktų queryset'ą, susietą su prisijungusiu
        ir patvirtintu tiekėju per StockRecord.
        """
        user = self.request.user
        try:
            # Naudojam related_name 'partner_profile'
            partner = user.partner_profile
            # Randame produktų ID, kurie turi stockrecord su šiuo partneriu
            product_ids = StockRecord.objects.filter(partner=partner).values_list('product_id', flat=True).distinct()
            # Grąžiname tuos produktus
            return Product.objects.filter(id__in=product_ids).prefetch_related(
                'stockrecords__partner', 'stockrecords__warehouse', # Optimizacija
                'attribute_values__attribute__option_group__options', # Pilnesni atributai
                'images', 'categories'
            )
        except Partner.DoesNotExist:
            # Turėtų neįvykti dėl permission_classes, bet apsidraudžiam
            return Product.objects.none()
        except AttributeError:
             # Jei user neturi partner_profile
             return Product.objects.none()


    def get_serializer_context(self):
        """ Perduodame partnerį į serializer'io kontekstą. """
        context = super().get_serializer_context()
        try:
            context['partner'] = self.request.user.partner_profile
        except (Partner.DoesNotExist, AttributeError):
             # Jei kyla problemų gaunant partnerį, kontekste jo nebus
             # Serializer'io validacija turėtų tai pagauti
             pass
        return context

    def perform_create(self, serializer):
        """
        Iškviečiama po serializer.is_valid() POST užklausoje.
        Serializeris pats atlieka produkto ir susijusių objektų kūrimą.
        Mes tik perduodame partnerį per kontekstą.
        """
        # Partneris jau yra kontekste, serializeris jį naudos savo create() metode
        serializer.save() # Kviečia ProductWriteSerializer.create()

    def perform_update(self, serializer):
        """
        Iškviečiama po serializer.is_valid() PUT/PATCH užklausoje.
        Serializeris pats atlieka atnaujinimą.
        """
        # Partneris jau yra kontekste, serializeris jį naudos savo update() metode
        serializer.save() # Kviečia ProductWriteSerializer.update()

    def perform_destroy(self, instance):
        """
        Iškviečiama DELETE užklausoje.
        Tikriname, ar prisijungęs partneris tikrai yra šio produkto
        stock įrašo savininkas prieš trindami.
        """
        user = self.request.user
        try:
            partner = user.partner_profile
            # Patikrinam, ar šis partneris turi stock record šiam produktui
            if StockRecord.objects.filter(product=instance, partner=partner).exists():
                # Galima trinti visą produktą, jei jis priklauso TIK šiam partneriui
                # Arba galbūt geriau tiesiog nustatyti num_in_stock = 0?
                # Kol kas triname produktą (atsargiai!)
                instance.delete()
                # Galima grąžinti 204 No Content statusą (ką ModelViewSet daro pagal nutylėjimą)
            else:
                # Jei partneris nėra savininkas (neturėtų įvykti dėl get_queryset)
                raise PermissionDenied("You do not have permission to delete this product.")
        except Partner.DoesNotExist:
             raise PermissionDenied("Partner profile not found.")
        except AttributeError:
             raise PermissionDenied("User does not have a partner profile.")