#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

# Standard Imports
import logging

# Non-Django 3rd Party Imports
import hoover

siggame_arena_json = "78fad6d2-34fd-4c36-98cc-eebf9adf2535"

handler = hoover.LogglyHttpHandler(token=siggame_arena_json)
log = logging.getLogger('Arena')
log.addHandler(handler)
log.setLevel(logging.DEBUG)
