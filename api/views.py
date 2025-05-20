from django.contrib.gis.db import models as gis_models
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from rest_framework import viewsets, status, serializers, generics # Pridedam status ir serializers
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
from .serializers import ProductWriteSerializer, ProductReadOnlySerializer, CustomTokenObtainPairSerializer, UserRegistrationSerializer, ProductDocumentSerializer # Importuojam abu
        # Importuojam reikalingas GIS funkcijas ir modelius
from django.db import models
from django.db.models import Q, Min
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D as GisDistance
from django.db.models.functions import Coalesce
from django.contrib.gis.geos import Point
from haystack.query import SearchQuerySet
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from django_elasticsearch_dsl_drf.constants import (
    LOOKUP_FILTER_RANGE,
    SUGGESTER_COMPLETION,
    LOOKUP_FILTER_TERMS,
)
from elasticsearch_dsl import A
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    CompoundSearchFilterBackend,
    OrderingFilterBackend,
    FacetedSearchFilterBackend,
)
from apps.catalogue.documents import ProductDocument  # Add this import

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


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = 'page_size'
    max_page_size = 100

# class PublicProductViewSet(HaystackViewSet):
#     index_models = [Product]
#     serializer_class = ProductHaystackSerializer # Serializeris pagrindiniams rezultatams
#     filter_backends = [HaystackFilter]
#     permission_classes = [permissions.AllowAny]
#     pagination_class = StandardResultsSetPagination
#     search_fields = ['text'] 

#     facet_serializer_class = CustomFacetSerializer

#     # Laukai rikavimui (turi būti 'sortable=True' indekse arba skaitiniai/datos)
#     ordering_fields = {
#         "title": "title", # Jei title indekse yra sortable
#         "date_created": "date_created",
#         "price": "price",
#         "relevance": "_score", # Specialus rikiavimas pagal relevantiškumą (kai yra 'q')
#     }
#     ordering = ['-date_created'] # Numatytasis rikiavimas

#     # Laukai facetavimui (turi būti 'faceted=True' indekse)
#     # URL parametrai facetiniam filtravimui paprastai bus tokie patys kaip laukų pavadinimai čia
#     # Pvz., ?category_slugs=gipso-plokstes&partner_name=Senukai
#     facet_fields = ['product_class_name', 'category_slugs', 'partner_name', 'condition', 'location_city']
#     # Galima nurodyti ir facetų parinktis, pvz., maksimalų grąžinamų facetų skaičių
#     # facet_options = {
#     #     'category_slugs': {'limit': 10, 'order': 'count'},
#     # }

#     # Serializeris facetų duomenims formuoti (jei norite keisti standartinį)
#     facet_serializer_class = CustomFacetSerializer # Naudojam savo arba standartinį HaystackFacetSerializer

#     # `list` metodas dabar turėtų automatiškai grąžinti ir facetus, jei naudojamas HaystackFacetFilter
#     # ir facet_serializer_class yra nustatytas.
#     # Facetai gali būti grąžinami kaip 'facets' raktas JSON atsakyme arba HTTP antraštėse.
#     # Patikrinkite drf-haystack dokumentaciją dėl tikslaus elgesio.

#     # Jei norite rankiniu būdu įtraukti facet'us į atsakymą (patikrinkite, ar tai būtina):
#     # def list(self, request, *args, **kwargs):
#     #     response = super().list(request, *args, **kwargs)
#     #     # queryset čia yra SearchQuerySet
#     #     queryset = self.filter_queryset(self.get_queryset())
#     #     # get_facets yra HaystackViewSet metodas
#     #     facets_data = self.get_facets(queryset)
#     #     if hasattr(response, 'data') and isinstance(response.data, dict) and facets_data:
#     #         response.data['facets'] = facets_data # Pridedam prie pagrindinio atsakymo
#     #     elif hasattr(response, 'data') and isinstance(response.data, list) and facets_data:
#     #         # Jei response.data yra sąrašas (kai nėra puslapiavimo), galim padaryti žodyną
#     #         response.data = {'results': response.data, 'facets': facets_data}
#     #     return response


#     @action(detail=False, methods=['get'])
#     def nearby(self, request):
#         latitude = request.query_params.get('lat')
#         longitude = request.query_params.get('lon')
#         radius_km = request.query_params.get('radius', "20")

#         if not latitude or not longitude:
#             return Response({"error": "Parameters 'lat' and 'lon' are required."}, status=status.HTTP_400_BAD_REQUEST)
#         try:
#             user_lat = float(latitude)
#             user_lon = float(longitude)
#             radius = float(radius_km)
#             user_point = Point(user_lon, user_lat, srid=4326)
#         except (TypeError, ValueError):
#             return Response({"error": "Invalid parameters."}, status=status.HTTP_400_BAD_REQUEST)

#         # Naudojam Haystack queryset'ą iš ViewSet'o
#         # get_queryset() grąžins SearchQuerySet().models(Product)
#         sqs = self.get_queryset().filter(is_public=True)
#         # 'location_point' turi būti apibrėžtas ProductIndex
#         sqs = sqs.dwithin('location_point', user_point, GisDistance(km=radius))
#         # Galima pridėti rikavimą pagal atstumą, jei Haystack ir ES backend'as tai palaiko
#         # sqs = sqs.distance('location_point', user_point).order_by('distance')

#         page = self.paginate_queryset(sqs) # HaystackViewSet paginate_queryset moka dirbti su SQS
#         if page is not None:
#             serializer = self.get_serializer(page, many=True) # Naudos ProductHaystackSerializer
#             return self.get_paginated_response(serializer.data)

#         serializer = self.get_serializer(sqs, many=True)
#         return Response(serializer.data)

# ... (PartnerProductViewSet ir CustomTokenObtainPairView lieka kaip anksčiau) ...


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
        




class PublicProductDocumentViewSet(DocumentViewSet):
    """
    Public API endpoint that allows products to be viewed, using Elasticsearch.
    """
    document = ProductDocument 
    serializer_class = ProductDocumentSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]

    filter_backends = [
        FilteringFilterBackend,
        CompoundSearchFilterBackend,  # Updated from SearchFilterBackend
        OrderingFilterBackend,
        FacetedSearchFilterBackend,
    ]

    # Updated faceted search fields configuration
    faceted_search_fields = {
        'categories': {
            'field': 'categories.slug.raw',
            'enabled': True,
            'options': {
                'size': 20,
                'min_doc_count': 1
            }
        },
        'condition': {
            'field': 'condition.raw',
            'enabled': True,
            'options': {
                'size': 10,
                'min_doc_count': 1
            }
        },
        'partner_name': {
            'field': 'partner_name.raw',
            'enabled': True,
            'options': {
                'size': 10,
                'min_doc_count': 1
            }
        },
        'price': {
            'field': 'price',
            'enabled': True,
            'options': {
                'aggs': {
                    'price_ranges': {
                        'range': {
                            'field': 'price',
                            'ranges': [
                                {'to': 10.0, 'key': '<10'},
                                {'from': 10.0, 'to': 50.0, 'key': '10-50'},
                                {'from': 50.0, 'to': 100.0, 'key': '50-100'},
                                {'from': 100.0, 'key': '>100'}
                            ]
                        }
                    }
                }
            }
        }
    }

    # Keep your existing configurations
    filter_fields = {
        'id': {
            'field': 'id',
            'lookups': ['exact', 'in'],
        },
        'title': {
            'field': 'title.raw',
            'lookups': ['exact', 'iexact', 'contains', 'icontains'],
        },
        'price': {
            'field': 'price',
            'lookups': ['exact', 'gte', 'lte', 'gt', 'lt', 'range'],
        },
        'categories': {
            'field': 'categories.slug.raw',
            'lookups': ['exact', 'in'],
        },
        'condition': {
            'field': 'condition.raw',
            'lookups': ['exact', 'in'],
        },
        'partner_name': {
            'field': 'partner_name.raw',
            'lookups': ['exact', 'in'],
        },
        'is_public': {
            'field': 'is_public',
            'lookups': ['exact'],
        }
    }

    search_fields = {
        'title': {'boost': 2},
        'description': None,
        'upc': None,
        'categories.name': None,
        'partner_name': None,
    }

    ordering_fields = {
        'title': 'title.raw',
        'price': 'price',
        'date_created': 'date_created',
    }
    ordering = ('-date_created',)