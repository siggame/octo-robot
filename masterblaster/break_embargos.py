#!/usr/bin/env python

import bootstrap

# My Imports
from thunderdome.models import Client

for client in Client.objects.all():
    client.embargoed = False
    client.save()
