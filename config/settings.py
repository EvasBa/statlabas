import os
import sys
import oscar
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured


from oscar.defaults import *
from datetime import timedelta

# Pridėkite savo aplikacijas prie Python kelio
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / '.env'
if env_path.is_file():
    load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.environ.get('SECRET_KEY', 'pakeiskite-veliau')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',

    
    'accounts.apps.AccountsConfig', # custom user model
    'profiles.apps.ProfilesConfig', # company profiles
   
    'locations.apps.LocationsConfig', # warehouse locations
    'api.apps.ApiConfig', # API app


    # Oscar apps 
    'oscar.config.Shop',
    'oscar.apps.analytics.apps.AnalyticsConfig',
    'oscar.apps.checkout.apps.CheckoutConfig',
    'oscar.apps.address.apps.AddressConfig',
    'oscar.apps.shipping.apps.ShippingConfig',
    #'oscar.apps.catalogue.apps.CatalogueConfig',
    'apps.catalogue.apps.CatalogueConfig',
    'oscar.apps.catalogue.reviews.apps.CatalogueReviewsConfig',
    'oscar.apps.communication.apps.CommunicationConfig',
    #'oscar.apps.partner.apps.PartnerConfig',
    'apps.partner.apps.PartnerConfig', # <<< Teisinga konfigūracija
    'oscar.apps.basket.apps.BasketConfig',
    'oscar.apps.payment.apps.PaymentConfig',
    'oscar.apps.offer.apps.OfferConfig',
    'oscar.apps.order.apps.OrderConfig',
    'apps.customer.apps.CustomerConfig',
    #'apps.oscar.apps.customer.apps.CustomerConfig', # <<< STANDARTINĖ OSCAR
    'oscar.apps.search.apps.SearchConfig',
    'oscar.apps.voucher.apps.VoucherConfig',
    'oscar.apps.wishlists.apps.WishlistsConfig',
    'oscar.apps.dashboard.apps.DashboardConfig',
    'oscar.apps.dashboard.reports.apps.ReportsDashboardConfig',
    'oscar.apps.dashboard.users.apps.UsersDashboardConfig',
    'oscar.apps.dashboard.orders.apps.OrdersDashboardConfig',
    'oscar.apps.dashboard.catalogue.apps.CatalogueDashboardConfig',
    'oscar.apps.dashboard.offers.apps.OffersDashboardConfig',
    #'oscar.apps.dashboard.partners.apps.PartnersDashboardConfig',
    'apps.dashboard.partners.apps.PartnersDashboardConfig',
    'oscar.apps.dashboard.pages.apps.PagesDashboardConfig',
    'oscar.apps.dashboard.ranges.apps.RangesDashboardConfig',
    'oscar.apps.dashboard.reviews.apps.ReviewsDashboardConfig',
    'oscar.apps.dashboard.vouchers.apps.VouchersDashboardConfig',
    'oscar.apps.dashboard.communications.apps.CommunicationsDashboardConfig',
    'oscar.apps.dashboard.shipping.apps.ShippingDashboardConfig',

    # 3rd-party apps
    'widget_tweaks',
    'haystack',
    'treebeard',
    'sorl.thumbnail',
    'django_tables2',
    'rest_framework',
    'rest_framework_simplejwt',
    'django.contrib.gis', # PostGIS
    'django_filters', # Django Filter
]

SITE_ID = 1
AUTH_USER_MODEL = 'accounts.CustomUser'
OSCAR_CUSTOM_APPS = True
OSCAR_PRODUCT_MODEL = 'catalogue.Product' # Nurodo, kad naudojame savo katalogo modelį
OSCAR_STOCKRECORD_MODEL = 'partner.StockRecord' # Nurodo, kad naudojame savo sandėlio modelį

AUTHENTICATION_BACKENDS = (
    'oscar.apps.customer.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'oscar.apps.basket.middleware.BasketMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            os.path.join(oscar.__path__[0], 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.checkout.context_processors.checkout',
                'oscar.apps.communication.notifications.context_processors.notifications',
                'oscar.core.context_processors.metadata',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis', # PostGIS
        'NAME': os.environ.get('DB_NAME', 'oscardb'), # Naujas vardas
        'USER': os.environ.get('DB_USER', 'oscaruser'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
if not DEBUG and not DATABASES['default'].get('PASSWORD'):
    raise ImproperlyConfigured("DB_PASSWORD must be set for production.")

HAYSTACK_CONNECTIONS = { 'default': { 'ENGINE': 'haystack.backends.simple_backend.SimpleEngine' } }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

# JWT Authentication settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY', SECRET_KEY),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
}
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

OSCAR_SHOP_NAME = 'Statulab Clean'
OSCAR_SHOP_TAGLINE = 'Fresh Start'
OSCAR_DEFAULT_CURRENCY = 'EUR'
# Apibrėžia privalomus laukus adreso formoje
OSCAR_REQUIRED_ADDRESS_FIELDS = (
    'first_name',
    'last_name',
    'line1',
    'city',
    'postcode',
    'country'
)
# Nurodo klasę, kurią Oscar naudoja dinamiškam klasių įkėlimui
#OSCAR_DYNAMIC_CLASS_LOADER = 'oscar.core.loading.DjangoOscarCoreDynamicClassLoader'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO', # Rodyti INFO ir aukštesnio lygio pranešimus
    },
    'loggers': {
        'api': { # Jūsų API aplikacijos loggeris
            'handlers': ['console'],
            'level': 'DEBUG', # Rodyti DEBUG pranešimus iš api app
            'propagate': True,
        },
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}