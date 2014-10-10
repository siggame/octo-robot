from thunderdome.models import Match
from pprint import pprint
from copy import deepcopy
import random
import jsonschema
import json

loop = 0

schema = {
    "description" : "Match result",
    "id" : "match",
    "type" : "object",
    "required" : ["winner", "log_location", "previous_matches"],
    "properties" : {
        "match_id" : { 
            "type" : "string",
        },
        "winner" : {
            "type" : "string",
        },
        "log_location" : {
            "type" : "string",
        },
        "previous_matches" : {
            "type" : "array",
            "items" : {
                "type" : "object",
                "minItems" : 2,
                "maxItems" : 2,
                "$ref" : "match",
            }
        }
    }
}

def main():
    tournament_id = 20133422
    championship = Match.objects.get(root=True, tournament=tournament_id)

    k = {}
    update_brackets(k, championship, 0)
    jsonschema.validate(k, schema)
    print json.dumps(k, indent=4)

def get_best_gamelog(match):
    games = list(match.games.all())
    if games:
        return random.choice(games).gamelog_url
    else:
        return "none"


id_array = {}

def update_brackets(parent_node, match, depth):
    global loop
    global id_array
    father_dict = {}
    mother_dict = {}
    my_dict = {}
    my_dict.update({"winner" : match.winner.name, 
                    "match_id" : str(match.pk),
                    "log_location" : get_best_gamelog(match),
                    "previous_matches" : []})

    loop += 1
    parent_node.update(my_dict)

    id_array.update({match.pk : my_dict})
    
    if match.father and match.father.pk in id_array.keys():
        my_dict["previous_matches"].append(id_array[match.father.pk])
        return

    if match.father and match.father.pk not in id_array.keys():
        my_dict["previous_matches"].append(father_dict)
        update_brackets(father_dict, match.father, depth+1)
    
    if match.mother and match.mother.pk in id_array.keys():
        my_dict["previous_matches"].append(id_array[match.mother.pk])
        return

    if match.mother and match.mother.pk not in id_array.keys():
        my_dict["previous_matches"].append(mother_dict)
        update_brackets(mother_dict, match.mother, depth+1)

if __name__ == "__main__":
    main()
