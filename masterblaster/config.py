#!/usr/bin/env python
# Configuration file for the arena
# also integrates bootstrap.py written by Stephen Jackson <scj7t4@mst.edu>

from aws_secrets import access_cred, secret_cred

game_name = 'megaminerai-9-space'
beanstalk_host = 'arena.mnuck.com'
arena_ami = 'ami-1e32ea77'
tournament_ami = 'ami-????????'
req_queue_len = 5

django_path = ['/django', '/django/siggame']

import sys
sys.path = django_path + sys.path
from django.core.management import setup_environ
import settings
setup_environ(settings)


import hoover
import logging

siggame_arena = "1c69bafa-5262-4c19-b8a7-630f3de4f8b3"
siggame_arena_json = "78fad6d2-34fd-4c36-98cc-eebf9adf2535"

handler = hoover.LogglyHttpHandler(token=siggame_arena_json)
log = logging.getLogger('Arena')
log.addHandler(handler)
log.setLevel(logging.DEBUG)
