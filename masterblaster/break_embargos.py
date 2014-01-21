
# My Imports
from thunderdome.models import Client

def break_embargos():
  for client in Client.objects.all():
    client.embargoed = False
    client.save()

if __name__ == "__main__":
  break_embargos()
