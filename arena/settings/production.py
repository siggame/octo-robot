
from arena.settings import *

SITE_ID = 2

USE_X_FORWARDED_HOST = True

DATABASES = {
    'default' : { 
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME' : POSTGRES_DB,
        'USER' : POSTGRES_USER,
        'PASSWORD' : POSTGRES_PASSWORD,
        'HOST': 'localhost',
     }
}

CACHES = {
    'default' : {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION' : [MEMCACHED_LOCATION],
     }
}

