
# My Imports
from thunderdome.models import Client

def embargo_shellai():
  for client in Client.objects.all():
    if client.current_tag.lower() == 'shellai':
      client.embargoed = True
      client.embargo_reason = 'You are running Shell AI'
      client.save()

if __name__ == "__main__":
  embargo_shellai()
