import os, sys

PROJECT_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(PROJECT_DIR, 'apps'),)
PUBLIC_DIR = os.path.join(PROJECT_DIR, '..', '..', 'public')

DEBUG = False
TEMPLATE_DEBUG = False

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

import djcelery
djcelery.setup_loader()

MANAGERS = ADMINS

TIME_ZONE = 'Etc/UTC'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_ROOT = os.path.join(PUBLIC_DIR, 'media')

MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(PUBLIC_DIR, 'static')

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, 'static'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'healthpoints.urls'

WSGI_APPLICATION = 'healthpoints.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_DIR, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
)

FIXTURE_DIRS = (
    os.path.join(PROJECT_DIR, 'fixtures'),
)

LOCALE_PATHS = (
    os.path.join(PROJECT_DIR, '..', 'locale'),
)

PROJECT_APPS = (
    'profiles',
    'tracks'
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.gis',
    'django_extensions',
    'south',
    'social.apps.django_app.default',
    'djcelery',
    'kombu.transport.django'
) + PROJECT_APPS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'social.backends.facebook.FacebookOAuth2',
    'social.backends.evernote.EvernoteSandboxOAuth',
    'profiles.backends.StravaOAuth2'
)

SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'publish_actions', 'publish_stream']

SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''


SOCIAL_AUTH_EVERNOTE_KEY = ''
SOCIAL_AUTH_EVERNOTE_SECRET = ''
NOTEBOOK_NAME = 'HealthPoints'


SOCIAL_AUTH_STRAVA_KEY = ''
SOCIAL_AUTH_STRAVA_SECRET = ''

MAPBOX_API_ENDPOINT = 'http://api.tiles.mapbox.com/v4'
MAPBOX_API_TOKEN = ''
MAPBOX_MAP_ID = ''


LOGIN_REDIRECT_URL = '/'

BROKER_URL = 'django://'
try:
    from settings_local import *
except ImportError:
    pass
