
import requests
import json

from thunderdome.config import api_url_template, game_name
from thunderdome.config import WEBSITE_USER_NAME, WEBSITE_ARENA_PASSWORD
from thunderdome.models import Client

def update_clients(api_url=None, auth=None):
    '''update the database with the current clients, based on game_name'''
    if api_url is None:
        api_url = api_url_template + game_name

    if auth is None:
        r = requests.get(api_url, auth=(WEBSITE_USER_NAME, WEBSITE_ARENA_PASSWORD))

    try:
        data = json.loads(r.text)
    except ValueError:
        print "couldn't parse text to json"
        return
    
    # check if got an invalid password login
    if r.status_code != 200:
        print "Error when attempting to pull clients data", r.status_code
        print data
        return 

    # list of clients that are found on the webserver
    updated_clients = []
    
    for block in data:
        if block['team'] is None or block['repository'] is None or block['tag'] is None:
            continue
        if Client.objects.filter(name=block['team']['slug']).count() == 0:
            client = makeClient(block)
        else:
            client = Client.objects.get(name=block['team']['slug'])        
            client.eligible = block['team']['eligible_to_win']
        if client.current_version != block['tag']['name']:
            client.embargoed = False # this is the only place embargoed can be broken
            client.current_version = block['tag']['name']

        client.save()
        updated_clients.append(client)

    current_clients = list(Client.objects.all()) # list of all clients
    missing_clients = [x for x in current_clients if x not in updated_clients] # list of clients not in the updated list
    if missing_clients:
        print "missing clients, deleting"
        for i in missing_clients:
            i.missing = True
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
    client.missing = False
    client.game_name = game_name
    client.save()
    return client


if __name__ == "__main__":
    update_clients()
