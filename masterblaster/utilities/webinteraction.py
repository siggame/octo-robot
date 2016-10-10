
import requests
import json

from thunderdome.config import api_url_template, game_name
from thunderdome.config import WEBSITE_USER_NAME, WEBSITE_ARENA_PASSWORD
from thunderdome.models import Client

# requests.packages.urllib3.disable_warnings()

def test_api(custom_game_name):
    api_url = api_url_template + custom_game_name
    print "Get on", api_url
    r = requests.get(api_url, auth=(WEBSITE_USER_NAME, WEBSITE_ARENA_PASSWORD), verify=False)
    
    print r.status_code
    print r.text
    print r.json()

def update_clients(api_url=None):
    '''update the database with the current clients, based on game_name'''
    if api_url is None:
        api_url = api_url_template + game_name
        r = requests.get(api_url, auth=(WEBSITE_USER_NAME, WEBSITE_ARENA_PASSWORD), verify=False)
    else:
        print "Attempting to get clients from", api_url
        r = requests.get(api_url)
        
    try:
        data = json.loads(r.text) # TODO: change this to r.json()
    except ValueError:
        print WEBSITE_USER_NAME
        print WEBSITE_ARENA_PASSWORD
        print api_url
        print r.text
        print "couldn't parse text to json"
        return
    
    # check if got an invalid password login
    if r.status_code != 200: 
        print "website error code", r.status_code
        print data
        return

    update_clients_from_data_block(data)
    print "Clients updated!"
    return
    
def update_clients_from_data_block(data):
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
            if client.missing:
                client.rating = 1800.0
                client.missing = False
            client.repo = block['repository']['path']
        if client.current_version != block['tag']['commit']:
            client.embargoed = False # this is the only place an embargo can be broken
            client.embargo_reason = ''
            client.current_version = block['tag']['commit']
            client.language = block['language']
        else:
            if client.embargoed and client.rating > 500:
                client.rating -= 1.0

        client.save()
        updated_clients.append(client)

    current_clients = list(Client.objects.all()) # list of all clients
    missing_clients = [x for x in current_clients if x not in updated_clients] # list of clients not in the updated list
    if missing_clients:
        for i in missing_clients:
            if i.missing == False:
                print i.name, "is missing, marking as missing"
            i.missing = True
            i.rating = 1
            i.save()
            
def makeClient(block):
    '''Make a client object from the provided API data block'''
    client = Client.objects.create()
    client.name = block['team']['slug']
    client.current_version = block['tag']['commit']
    client.repo = block['repository']['path']    
    client.stats = ''
    client.embargoed = False
    client.eligible = block['team']['eligible_to_win']
    client.seed = 0
    client.missing = False
    client.game_name = game_name
    client.language = block['language']
    client.save()
    return client


if __name__ == "__main__":
    update_clients()
