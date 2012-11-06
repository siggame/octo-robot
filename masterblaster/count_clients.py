#!/usr/bin/env python


# My Imports
import bootstrap
from thunderdome.models import Client

clients = list(Client.objects
               .filter(eligible=True)
               .filter(embargoed=False))
print clients
print len(clients)
