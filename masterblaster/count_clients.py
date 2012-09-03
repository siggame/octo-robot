#!/usr/bin/env python

import bootstrap

# My Imports
from thunderdome.models import Client

clients = list(Client.objects \
                   .filter(eligible=True) \
                   .filter(embargoed=False))
print clients
print len(clients)