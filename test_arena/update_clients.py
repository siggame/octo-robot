from thunderdome.models import Client
from test_arena.username_web_parser import get_all_forks, repo_username
from thunderdome.config import game_name
import json

def update_clients():
    subs = game_name.split("-")
    repo_name = game_name.split("-")[::-1][0]
    updated_clients = []
    for i in get_all_forks(repo_name):
        print i
        print "user name", repo_username(i)
        user_name = repo_username(i)
        if Client.objects.filter(name=user_name).count() == 0:
            client = makeClient(i, user_name)
        else:
            client = Client.objects.get(name=user_name)
        updated_clients.append(client)

    current_clients = list(Client.objects.all())
    missing_clients = [x for x in current_clients if x not in updated_clients]
    if missing_clients:
        print "missing clients, deleting"
    for i in missing_clients:
        i.missing = True
        i.save()


def makeClient(url, client_name):
    client = Client.objects.create()
    client.name = client_name
    client.current_version = "master"
    client.repo = url
    client.stats = json.dumps({"language" : "any"})
    client.missing = False
    client.game_name = game_name
    client.embargoed = False
    client.eligible = True
    client.save()
    return client

if __name__ == "__main__":
    update_clients_from_github()
