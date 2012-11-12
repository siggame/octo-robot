#!/usr/bin/env python
### Missouri S&T ACM SIG-Game Arena (Thunderdome)
#####

import bootstrap

# My Imports
from thunderdome.models import Client

def seed():

	for client in Client.objects.all():
  	  client.seed = -1
	  client.save()

	### assign seeds
	clients = list(Client.objects \
		                 .filter(eligible=True) \
			             .filter(embargoed=False))
	clients.sort(reverse = True, key = lambda x: x.fitness())

	for (i, client) in enumerate(clients, 1):
  	  client.seed = i
	  client.save()

seed()

