
from arena.settings.defaults import *

SITE_ID = 1
DEBUG=True
TEMPLATE_DEBUG=DEBUG

DATABASES = {
    'default' : {
        'ENGINE' : 'django.db.backends.sqlite3',
        'NAME' : os.path.join(VAR_DIR, "db", "arena.db"),
    }
}


