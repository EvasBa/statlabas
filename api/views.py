from django.contrib.gis.db import models as gis_models
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from rest_framework import viewsets, status, serializers, generics # Pridedam status ir serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_haystack.viewsets import HaystackViewSet
from drf_haystack.filters import HaystackFilter, HaystackFacetFilter
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
from .serializers import ProductWriteSerializer, ProductReadOnlySerializer, CustomTokenObtainPairSerializer, UserRegistrationSerializer, ProductHaystackSerializer # Importuojam abu
        # Importuojam reikalingas GIS funkcijas ir modelius
from django.db import models
from django.db.models import Q, Min
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D as GisDistance
from django.db.models.functions import Coalesce
from django.contrib.gis.geos import Point
from haystack.query import SearchQuerySet

# logging
import logging
logger = logging.getLogger(__name__)

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


class PublicProductViewSet(HaystackViewSet):
    index_models = [Product] # Nurodom, kad indeksuosim Product modelį
    serializer_class = ProductHaystackSerializer # Naudojam mūsų serializerį
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    # Naudojam mūsų sukurtą filtrų klasę
    filter_backends = (HaystackFilter, filters.OrderingFilter)
    ordering_fields = ['title', 'date_created', 'price'] # Laukai, pagal kuriuos galima rikiuoti
    ordering = ['-date_created'] # Numatytasis rikiavimas
    facet_fields = ['categories', 'category_slug'] # Laukai, pagal kuriuos bus facet'ai <--- Papildyti
    
    
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

    # --- Geografinės Paieškos Metodas (Pridedam kaip veiksmą) ---
    # Šis metodas leidžia ieškoti produktų pagal geografinę vietą
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lon')
        radius_km = request.query_params.get('radius', 20)

        if not latitude or not longitude:
            return Response(
                {"error": "Parameters 'lat' and 'lon' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user_lat = float(latitude)
            user_lon = float(longitude)
            radius = float(radius_km)
            # Svarbu: Haystack .dwithin() tikisi Django GIS Point objekto
            user_point = Point(user_lon, user_lat, srid=4326)
        except (TypeError, ValueError):
            return Response({"error": "Invalid parameters."}, status=status.HTTP_400_BAD_REQUEST)

        # Sukuriame SearchQuerySet
        # Įsitikinkite, kad jūsų ProductIndex turi LocationField pavadinimu 'location_point'
        # ir prepare_location_point metodą.
        sqs = SearchQuerySet().models(Product).filter(is_public=True) # Pradedam nuo viešų produktų
        # Atliekame geografinę paiešką
        sqs = sqs.dwithin('location_point', user_point, GisDistance(km=radius))
        # Pastaba: 'location_point' yra pavyzdinis pavadinimas lauko jūsų ProductIndex.
        # Jį reikia apibrėžti ProductIndex:
        # location_point = indexes.LocationField(null=True)
        # def prepare_location_point(self, obj): ... grąžina GIS Point ...

        # Puslapiavimas Haystack rezultatams
        # HaystackViewSet turi savo puslapiavimo logiką, bet čia mes darome custom action
        # Todėl reikia rankiniu būdu puslapiuoti
        page = self.paginate_queryset(list(sqs)) # Svarbu konvertuoti į sąrašą prieš puslapiuojant Haystack SQS

        if page is not None:
            # Svarbu: HaystackViewSet.get_serializer laukia SearchResult objektų.
            # Jei norime naudoti ProductReadOnlySerializer, reikia perduoti Django objektus.
            # Tačiau, jei page yra sąrašas SearchResult, reikia HaystackSerializer.
            # Kadangi naudojame HaystackViewSet, get_serializer turėtų veikti su SearchResult.
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Jei nėra puslapiavimo (retai pasitaiko su HaystackViewSet)
        serializer = self.get_serializer(list(sqs), many=True) # Konvertuojam į sąrašą
        return Response(serializer.data)


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

class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny] # Leidžiam registruotis visiems

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save() # Iškviečia serializer.create()
            headers = self.get_success_headers(serializer.data)

            # --- Generuojame JWT tokenus po sėkmingos registracijos ---
            logger.info(f"Registration successful for {user.email}. Generating tokens.")
            try:
                refresh = RefreshToken.for_user(user)
                # TODO: Apsvarstyti, ar grąžinti tokenus su custom claims iškart.
                # Kol kas grąžinam standartinius.
                data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    # Galima grąžinti ir dalį vartotojo duomenų
                    'user': {
                        'id': user.pk,
                        'email': user.email,
                        'user_type': user.user_type
                    }
                }
                return Response(data, status=status.HTTP_201_CREATED, headers=headers)
            except Exception as e:
                 # Jei nepavyksta generuoti tokenų (neturėtų nutikti)
                 logger.error(f"Could not generate tokens for user {user.email} after registration: {e}", exc_info=True)
                 # Grąžinam sėkmę, bet be tokenų - vartotojas turės prisijungti atskirai
                 return Response(
                     {"message": "Registration successful, but could not log you in automatically. Please log in."},
                     status=status.HTTP_201_CREATED,
                     headers=headers
                 )

        except serializers.ValidationError as e:
            logger.warning(f"Registration validation failed: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e: # Kitos netikėtos klaidos
             logger.error(f"Unexpected error during registration: {e}", exc_info=True)
             return Response({"error": "An unexpected error occurred during registration."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)