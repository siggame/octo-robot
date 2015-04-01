from thunderdome.models import Client
from test_arena.username_web_parser import get_all_forks, repo_username
from thunderdome.config import game_name

def update_clients_from_github():
    subs = game_name.split("-")
    repo_name = game_name.split("-")[::-1][0]
    for i in get_all_forks(repo_name):
        print i
        print "user name", repo_username(i)
        


if __name__ == "__main__":
    update_clients_from_github()
