from arena.settings.secret_settings import GITHUB_API_TOKEN

import requests
import json
import random
import re
from masterblaster.utilities.webinteraction import update_clients_from_data_block

def main(fork_list, random_count=4):
    header_info = {"Authorization" : "token %s" % GITHUB_API_TOKEN}
    base_api_uri = "https://api.github.com"
    test_clients = []
    game_name = "MegaMinerAI-16-Anarchy"
    for fork in fork_list:
        forks_url = requests.get("%s/repos/siggame/%s/forks" % (base_api_uri, fork), headers=header_info)
        if "message" in forks_url.json():
            if forks_url.json()["message"] == "Bad credentials":
                print "Error I require a valid GITHUB_API_TOKEN"
                print "In order to make a GITHUB_API_TOKEN go here https://github.com/blog/1509-personal-api-tokens"
                return
        data = forks_url.json()
        for i in data:
            master_hash = requests.get("%s/repos/%s/commits/master" % (base_api_uri, i["full_name"]), headers=header_info)
            test_clients.append(construct_client_block("master", master_hash.json()["sha"], i["full_name"] + ".git",
                                                       i["owner"]["login"], i["language"].lower()))
            
        base_repo_uri = "%s/repos/siggame/%s" % (base_api_uri, fork)
        base_repo_request = requests.get(base_repo_uri, headers=header_info)
        base_repo_json = base_repo_request.json()
        shellai_uri = "%s/repos/siggame/%s/commits/%s-ShellAI" % (base_api_uri, fork, game_name)
        shellai_hash = requests.get(shellai_uri, headers=header_info)
        add_shell_ai = True
        if "message" in shellai_hash.json().keys():
            if shellai_hash.json()["message"] == "Not Found":
                print "Error no shell ai for", fork
                add_shell_ai = False

        if add_shell_ai:
            test_clients.append(construct_client_block("%s-ShellAI" % (game_name),
                                                       shellai_hash.json()["sha"],
                                                       base_repo_json["full_name"] + ".git",
                                                       base_repo_json["owner"]["login"] + "_" + base_repo_json["language"],
                                                       base_repo_json["language"]))

    print "Generating", random_count, "random clients"
    for i in range(random_count):
        test_clients.append(construct_random_client(test_clients[random.randint(0,len(test_clients)-1)]))
        
    # the shell ai branches

    for i in test_clients:
        print "Adding team", i["team"]["slug"]

    update_clients_from_data_block(test_clients) # remember if the commit hash doesn't change then the client will not be unembargoed


def construct_client_block(tag_name, tag_commit, repo_path, team_slug, language):
    return {"tag": {"name" : tag_name, "commit" : tag_commit},
            "repository" : {"path" : repo_path},
            "team" : {"slug" : team_slug, "eligible_to_win" : "true"}, # todo add in non eligible teams, maybe randomize it? 
            "language" : language
           }


def construct_random_client(client_block):
    clone = dict(client_block)
    
    if not ("clone_id" in clone.keys()): # clone id is only used for generating new / more test clients
        clone["clone_id"] = 1
        clone["team"]["slug"] = clone["team"]["slug"] + "_" + str(clone["clone_id"])
    else:
        clone["clone_id"] += 1
        clone["team"]["slug"] = clone["team"]["slug"].split("_")[0] + "_" + str(clone["clone_id"] )

    return clone

if __name__ == "__main__":
    fork_list = ["Joueur.py-MegaMinerAI-Dev", "Joueur.lua-MegaMinerAI-Dev", "Joueur.js-MegaMinerAI-Dev",
                 "Joueur.java-MegaMinerAI-Dev", "Joueur.cpp-MegaMinerAI-Dev", "Joueur.cs-MegaMinerAI-Dev"]
    main(fork_list, 0)
