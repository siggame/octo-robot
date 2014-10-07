
import requests
import json

from thunderdome.config import api_url_template, game_name
from thunderdome.config import WEBSITE_USER_NAME, WEBSITE_ARENA_PASSWORD
from thunderdome.models import Client

def update_clients():
    '''update the database with the current clients, based on game_name'''
    api_url = api_url_template % game_name
    r = requests.get(api_url, auth=(WEBSITE_USER_NAME, WEBSITE_ARENA_PASSWORD))
    try:
        data = json.loads(r.text)
    except ValueError:
        data = []
        print r.text
    
    updated_clients = []
    
    for block in data:
        if block['team'] is None or block['repository'] is None or block['tag'] is None:
            continue
        if Client.objects.filter(name=block['team']['slug']).count() == 0:
            client = makeClient(block)
        else:
            client = Client.objects.get(name=block['team']['slug'])        
            #client.eligible = block['team']['eligible_to_win']
        if client.current_version != block['tag']['name']:
            client.embargoed = False # this is the only place embargoed can be broken
            client.current_version = block['tag']['name']
        client.save()
        updated_clients.append(client)

    current_clients = list(Client.objects.all())
    missing_clients = [x for x in current_clients if x not in updated_clients]
    print "Missing clients"
    for i in missing_clients:
        print i.name
        c_stats = json.loads(i.stats)
        c_stats['missing'] = True
        i.stats = json.dumps(c_stats)
        i.save()
    
def update_clients_from(api_url):
    r = requests.get(api_url)
    try:
        data = json.loads(r.text)
    except ValueError:
        data = []
        print r.text
    
    updated_clients = []
    
    for block in data:
        if block['team'] is None or block['repository'] is None or block['tag'] is None:
            continue
        if Client.objects.filter(name=block['team']['slug']).count() == 0:
            client = makeClient(block)
        else:
            client = Client.objects.get(name=block['team']['slug'])        
            #client.eligible = block['team']['eligible_to_win']
        if client.current_version != block['tag']['name']:
            client.embargoed = False # this is the only place embargoed can be broken
            client.current_version = block['tag']['name']
        client.save()
        updated_clients.append(client)

    current_clients = list(Client.objects.all())
    missing_clients = [x for x in current_clients if x not in updated_clients]
    print "Missing clients"
    for i in missing_clients:
        print i.name
        c_stats = json.loads(i.stats)
        c_stats['missing'] = True
        i.stats = json.dumps(c_stats)
        i.save()

def makeClient(block):
    '''Make a client object from the provided API data block'''
    client = Client.objects.create()
    client.name = block['team']['slug']
    client.current_version = block['tag']['name']
    client.repo = block['repository']['path']    
    client.stats = json.dumps({"language" : block['language']})
    client.embargoed = False
    client.eligible = block['team']['eligible_to_win']
    client.seed = 0
    client.save()
    return client


if __name__ == "__main__":
    update_clients()
