"""
Configuration file for the arena to try and limit the repeated code.

@author Stephen Jackson <scj7t4@mst.edu>
"""

from config import django_path

import sys
sys.path = django_path + sys.path
from django.core.management import setup_environ
import settings
setup_environ(settings)
