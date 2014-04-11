
import arena.settings.defaults as default_settings
from arena.settings.secret_settings import POSTGRES_NAME, POSTGRES_USER, POSTGRES_PASSWORD
from arena.settings.defaults import *

SITE_ID = 1
DEBUG = False 
USE_X_FORWARDED_HOST = True

DATABASES = {
    'default' : { 
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME' : POSTGRES_NAME,
        'USER' : POSTGRES_USER,
        'PASSWORD' : POSTGRES_PASSWORD,
        'HOST': 'localhost',
     }
}
