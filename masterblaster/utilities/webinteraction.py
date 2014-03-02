
import requests
import json

from thunderdome.config import api_url_template, game_name
from thunderdome.config import WEBSITE_USER_NAME, WEBSITE_ARENA_PASSWORD
from thunderdome.models import Client

def update_clients():
    print 'updating clients'
    api_url = api_url_template % game_name
    print api_url
    
    r = requests.get(api_url, auth=(WEBSITE_USER_NAME, WEBSITE_ARENA_PASSWORD))
    print r.text

    data = json.loads(r.text)

    for block in data:
        if block['team'] is None or block['repository'] is None or block['tag'] is None:
            continue
        if Client.objects.filter(name=block['team']['slug']).count() == 0:
            client = makeClient(block)
        else:
            client = Client.objects.get(name=block['team']['slug'])
        if client.current_version != block['tag']['name']:
            client.embargoed = False # this is the only place embargoed can be broken
            client.current_version = block['tag']['name']
            client.save()
            
    
def makeClient(block):
    '''Make a client object from the provided API data block'''

    client = Client.objects.create()
    client.name = block['team']['slug']
    client.current_version = block['tag']['name']
    client.repo = block['repository']['path']
    client.embargoed = False
    client.eligible = True
    client.seed = 0
    client.save()
    return client
