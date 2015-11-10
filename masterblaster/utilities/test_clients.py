from arena.settings.secret_settings import GITHUB_API_TOKEN

import requests
import json
from masterblaster.utilities.webinteraction import update_clients_from_data_block

def main(fork_lang_list):
    header_info = {"Authorization" : "token %s" % GITHUB_API_TOKEN}
    base_api_uri = "https://api.github.com"
    test_clients = []
    for fork, lang in fork_lang_list:
        forks_url = requests.get("%s/repos/siggame/%s/forks" % (base_api_uri, fork), headers=header_info)
        data = forks_url.json()
        for i in data:
            print "Adding client", i["full_name"]
            master_hash = requests.get("%s/repos/%s/commits/master" % (base_api_uri, i["full_name"]), headers=header_info)
            test_clients.append(construct_client_block("master", master_hash.json()["sha"], i["ssh_url"], i["login"], lang))

    print 'Test client'
    for i in test_clients:
        print 
        print i
        
    update_clients_from_data_block(test_clients)


def construct_client_block(tag_name, tag_commit, repo_path, team_slug, language):
    return {"tag": {"name" : tag_name, "commit" : tag_commit},
            "repository" : {"path" : repo_path},
            "team" : {"slug" : team_slug, "eligible_to_win" : "true"}, # todo add in non eligible teams, maybe randomize it? 
            "language" : language
           }


if __name__ == "__main__":
    fork_list = [("Joueur.py-MegaMinerAI-Dev", "python"), ("Joueur.lua-MegaMinerAI-Dev", "lua"),
                 ("Joueur.js-MegaMinerAI-Dev", "javascript"), ("Joueur.java-MegaMinerAI-Dev", "java"),
                 ("Joueur.cpp-MegaMinerAI-Dev", "c++"), ("Joueur.cs-MegaMinerAI-Dev", "csharp")]

    main(fork_list)
