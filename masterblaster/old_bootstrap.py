
import os
MASTERBLASTER_DIR = os.path.dirname(os.path.realpath(__file__))
BUILDOUT_DIR = os.path.dirname(MASTERBLASTER_DIR)
ARENA_DIR = os.path.join(BUILDOUT_DIR, "arena")

django_path = [ARENA_DIR, os.path.join(ARENA_DIR, "arena")]

import sys
print sys.path
import settings


#sys.path = django_path + sys.path
from django.core.management import setup_environ
import settings
setup_environ(settings)
