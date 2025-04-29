from django.contrib.gis.db import models as gis_models
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from rest_framework import viewsets, status, serializers # Pridedam status ir serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from oscar.core.loading import get_model
from .filters import ProductFilter # Importuojam mūsų filtrų klasę
from django_filters.rest_framework import DjangoFilterBackend
# Importuojam mūsų leidimų klasę
from .permissions import IsVerifiedPartnerPermission
from django.core.exceptions import PermissionDenied
# Importuojam mūsų serializer'ius
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework import permissions, filters, viewsets
from .serializers import ProductWriteSerializer, ProductReadOnlySerializer, CustomTokenObtainPairSerializer # Importuojam abu
        # Importuojam reikalingas GIS funkcijas ir modelius
from django.db import models
from django.db.models import Q, Min
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models.functions import Coalesce
from django.contrib.gis.geos import Point


# Importuojam modelius
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')
Partner = get_model('partner', 'Partner')

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer


class StandardResultsSetPagination(PageNumberPagination): # Klasė puslapiavimui
    page_size = 24 # Kiek įrašų per puslapį
    page_size_query_param = 'page_size'
    max_page_size = 100


class PublicProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductReadOnlySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    queryset = Product.objects.filter(is_public=True).prefetch_related(
        'stockrecords__partner', 'stockrecords__warehouse',
        'attribute_values__attribute__option_group__options',
        'images', 'categories'
    ).select_related('product_class').distinct()

    # --- Pridedame Filtravimą, Paiešką, Rikiavimą ---
    filter_backends = [
        DjangoFilterBackend, # Mūsų sukurtiems filtrams
        filters.SearchFilter,  # Paieškai
        filters.OrderingFilter # Rikiavimui
    ]
    filterset_class = ProductFilter # Nurodom mūsų filtrų klasę

    search_fields = [ # Laukai, pagal kuriuos ieškosime ( регистрo nejautri paieška)
        'title',
        'description',
        'upc',
        'stockrecords__partner__name', # Pagal tiekėjo vardą
        'categories__name', # Pagal kategorijos pavadinimą
        # Galima pridėti atributus, bet gali būti lėta:
        # 'attribute_values__value_text',
        # 'attribute_values__value_option__option',
    ]

    ordering_fields = [ # Laukai, pagal kuriuos galima rikiuoti (pvz., ?ordering=price)
        'title',
        'date_created',
        # Rikiavimas pagal kainą (imama mažiausia kaina iš stockrecords)
        # Reikia anotacijos, todėl paprasčiau pridėti prie ordering
        # 'stockrecords__price', # Tai rikiuos pagal visus stockrecordus, ne pagal mažiausią kainą
        'price' # Pridėsime anotaciją žemiau
    ]
    ordering = ['-date_created'] # Numatytasis rikiavimas

    def get_queryset(self):
        """ Anotuojame queryset'ą su mažiausia kaina rikiavimo galimybei. """
        queryset = super().get_queryset()
        # Anotuojame su mažiausia kaina iš susijusių stockrecords
        from django.db.models import Min
        queryset = queryset.annotate(
            price=Min('stockrecords__price') # Naudojam 'price' lauką iš StockRecord
        )
        return queryset

    # --- Geografinės Paieškos Metodas (Pridedam kaip veiksmą) ---
    # Šis metodas leidžia ieškoti produktų pagal geografinę vietą
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Find products near a given location.
        
        Query Parameters:
            lat (float): Latitude of the search point
            lon (float): Longitude of the search point
            radius (float): Search radius in kilometers (default: 5)
            
        Returns:
            Paginated list of products ordered by distance
        """
    # Get and validate parameters
        try:
            user_lat = float(request.query_params.get('lat'))
            user_lon = float(request.query_params.get('lon'))
            radius = float(request.query_params.get('radius', 5))
        except (TypeError, ValueError):
            return Response(
                {"error": "Valid latitude, longitude, and radius are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create user location point
        try:
            user_point = Point(user_lon, user_lat, srid=4326)
        except Exception as e:
            return Response(
                {"error": f"Could not create location point: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Find products with stock records near the location
            nearby_stockrecords = StockRecord.objects.select_related(
                'warehouse', 'partner', 'product'
            ).annotate(
                effective_location=Coalesce(
                    'warehouse__location',
                    'partner__default_location',
                    output_field=gis_models.PointField()
                )
            ).annotate(
                distance=Distance('effective_location', user_point)
            ).filter(
                Q(warehouse__location__isnull=False) | 
                Q(partner__default_location__isnull=False),
                product__is_public=True,
                num_in_stock__gt=0
            ).filter(
                distance__lte=D(km=radius)
            ).order_by('distance')

            # Get unique product IDs with their minimum distance
            product_ids = nearby_stockrecords.values_list('product_id', flat=True).distinct()

            # Get full product details with minimum distance
            queryset = self.get_queryset().filter(
                id__in=product_ids
            ).annotate(
                min_distance=Min(
                    Distance(
                        Coalesce(
                            'stockrecords__warehouse__location',
                            'stockrecords__partner__default_location'
                        ),
                        user_point
                    )
                )
            ).order_by('min_distance')

            # Apply pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PartnerProductViewSet(viewsets.ModelViewSet):
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
    
    def get_serializer_class(self):
        # Naudojam rašymo serializerį create/update veiksmams
        if self.action in ['create', 'update', 'partial_update']:
            return ProductWriteSerializer
        # Visiems kitiems (list, retrieve) naudojam skaitymo serializerį
        return ProductReadOnlySerializer

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