from arena.settings.secret_settings import GITHUB_API_TOKEN

import requests
import json
from masterblaster.utilities.webinteraction import update_clients_from_data_block

def main(fork_list):
    header_info = {"Authorization" : "token %s" % "None"}
    base_api_uri = "https://api.github.com"
    test_clients = []
    for fork in fork_list:
        forks_url = requests.get("%s/repos/siggame/%s/forks" % (base_api_uri, fork), headers=header_info)
        print forks_url.json()
        if forks_url.json()["message"] == "Bad credentials":
            print "Error I require a valid GITHUB_API_TOKEN"
            print "In order to make a GITHUB_API_TOKEN go here https://github.com/blog/1509-personal-api-tokens"
            return 
        data = forks_url.json()
        for i in data:
            print "Adding client", i["owner"]["login"]
            master_hash = requests.get("%s/repos/%s/commits/master" % (base_api_uri, i["full_name"]), headers=header_info)
            test_clients.append(construct_client_block("master", master_hash.json()["sha"], i["ssh_url"],
                                                       i["owner"]["login"], i["language"].lower()))
        
    update_clients_from_data_block(test_clients)


def construct_client_block(tag_name, tag_commit, repo_path, team_slug, language):
    return {"tag": {"name" : tag_name, "commit" : tag_commit},
            "repository" : {"path" : repo_path},
            "team" : {"slug" : team_slug, "eligible_to_win" : "true"}, # todo add in non eligible teams, maybe randomize it? 
            "language" : language
           }


if __name__ == "__main__":
    fork_list = ["Joueur.py-MegaMinerAI-Dev", "Joueur.lua-MegaMinerAI-Dev", "Joueur.js-MegaMinerAI-Dev",
                 "Joueur.java-MegaMinerAI-Dev", "Joueur.cpp-MegaMinerAI-Dev", "Joueur.cs-MegaMinerAI-Dev"]
    main(fork_list)
