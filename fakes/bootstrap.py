#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
### written by Stephen Jackson <scj7t4@mst.edu>
#####

django_path = ['/home/ubuntu/siggame', '/home/ubuntu/siggame/siggame']

import sys
sys.path = django_path + sys.path
from django.core.management import setup_environ
import settings
setup_environ(settings)
