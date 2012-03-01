"""
Configuration file for the arena to try and limit the repeated code.

@author Stephen Jackson <scj7t4@mst.edu>
"""
DJANGO_PATH = '/home/scj7t4/arena'
DJANGO_CORE = None
BEANSTALK_SERVER = 'localhost'
BEANSTALK_PORT = 11300

import sys
sys.path = [DJANGO_PATH] + sys.path
if DJANGO_CORE != None:
    sys.path = [DJANGO_CORE] + sys.path

from django.core.management import setup_environ
import settings

setup_environ(settings)

    
