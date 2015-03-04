import os
import dj_database_url


# Basic settings

SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',') or []


# Static files
# http://whitenoise.evans.io/en/latest/#quickstart-for-django-apps

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'


# Database

DATABASE_URL = os.environ.get('DATABASE_URL', None)

if not DATABASE_URL:
    POSTGRES_IP = os.environ.get('POSTGRES_PORT_5432_TCP_ADDR', None)

    if POSTGRES_IP:
        POSTGRES_PORT = os.environ.get('POSTGRES_PORT_5432_TCP_PORT')
        POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
        POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', '')
        POSTGRES_DB = os.environ.get('POSTGRES_DB', '{{ cookiecutter.repo_name }}')
        POSTGRES_USE_POSTGIS = int(os.environ.get('POSTGRES_USE_POSTGIS', '0'))

        POSTGRES_BACKEND = 'postgis' if POSTGRES_USE_POSTGIS else 'postgres'

        POSTGRES_AUTH = POSTGRES_USER
        if POSTGRES_PASSWORD:
            POSTGRES_AUTH += ':' + POSTGRES_PASSWORD

        DATABASE_URL = '%s://%s@%s:%s/%s' % (
            POSTGRES_BACKEND,
            POSTGRES_AUTH,
            POSTGRES_IP,
            POSTGRES_PORT,
            POSTGRES_DB,
        )

    else:
        # Fallback to SQLite
        # Note: any database operations performed against this SQLite file will
        # not be perisisted between commands.
        DATABASE_URL = 'sqlite://{{ cookiecutter.repo_name }}.db'

DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL),
}


# Elasticsearch

ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL', None)

if not ELASTICSEARCH_URL:
    ELASTICSEARCH_IP = os.environ.get('ELASTICSEARCH_PORT_9200_TCP_ADDR', None)

    if ELASTICSEARCH_IP:
        ELASTICSEARCH_PORT = os.environ.get('ELASTICSEARCH_PORT_9200_TCP_PORT')
        ELASTICSEARCH_URL_PREFIX = os.environ.get('ELASTICSEARCH_URL_PREFIX', '/')

        ELASTICSEARCH_URL = 'http://%s:%s%s' % (
            ELASTICSEARCH_IP,
            ELASTICSEARCH_PORT,
            ELASTICSEARCH_URL_PREFIX,
        )

if ELASTICSEARCH_URL:
    ELASTICSEARCH_INDEX = os.environ.get('ELASTICSEARCH_INDEX', '{{ cookiecutter.repo_name }}')

    WAGTAILSEARCH_BACKENDS = {
        'default': {
            'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch',
            'URLS': [ELASTICSEARCH_URL],
            'INDEX': ELASTICSEARCH_INDEX,
        }
    }
else:
    WAGTAILSEARCH_BACKENDS = {
        'default': {
            'BACKEND': 'wagtail.wagtailsearch.backends.db.DBSearch',
        }
    }


# Redis

REDIS_LOCATION = os.environ.get('REDIS_LOCATION', None)

if not REDIS_LOCATION:
    REDIS_IP = os.environ.get('REDIS_PORT_6379_TCP_ADDR', None)

    if REDIS_IP:
        REDIS_PORT = os.environ.get('REDIS_PORT_6379_TCP_PORT')

        REDIS_LOCATION = '%s:%s' % (
            REDIS_IP,
            REDIS_PORT,
        )

if REDIS_LOCATION:
    REDIS_DB = int(os.environ.get('REDIS_DB', '0'))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
    REDIS_KEY_PREFIX = os.environ.get('REDIS_KEY_PREFIX', '{{ cookiecutter.repo_name }}')

    CACHES = {
        'default': {
            'BACKEND': 'redis_cache.cache.RedisCache',
            'LOCATION': REDIS_LOCATION,
            'KEY_PREFIX': REDIS_KEY_PREFIX,
            'OPTIONS': {
                'DB': REDIS_DB,
                'PASSWORD': REDIS_PASSWORD,
                'CLIENT_CLASS': 'redis_cache.client.DefaultClient',
            }
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

