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
        "player_1" : { 
            "type" : "string",
        },
        "player_2" : {
            "type" : "string",
        },
        "previous_matches" : {
            "type" : "array",
            "items" : {
                "minItems" : 2,
                "maxItems" : 2,
                "oneOf" : [
                    {
                        "type" : "object",
                        "$ref" : "match"
                    },
                    {
                        "type" : "integer",
                    }
                ]
            }
        }
    }
}

global_dict = {}

def main():
    tournament_id = 20133440
    championship = Match.objects.get(root=True, tournament=tournament_id)

    # k = {}
    # update_brackets(k, championship, 0)
    # jsonschema.validate(k, schema)
    # print json.dumps(k, indent=1)
    update_bracket(championship)
    print json.dumps(global_dict, indent=1)
    # keys = sorted(global_dict.keys(), key = lambda x : int(x))
    # for i in keys:
    #    print i, global_dict[i]


def get_best_gamelog(match):
    """
    This can be used to change what game gets visualized to during the tournament. 
    """
    games = list(match.games.all())
    if games:
        return random.choice(games).gamelog_url
    else:
        return "none"


id_array = {}



def update_bracket(match):
    prev_games = []

    global_dict.update({str(match.pk) : { "winner" : match.winner.name,
                                         "log_location" : get_best_gamelog(match),
                                         "previous_matches" : prev_games,
                                         "player_1" : match.p0.name,
                                          "player_2" : match.p1.name}})
    
    if match.father:
        prev_games.append(match.father.pk)
        update_bracket(match.father)
        
    if match.mother:
        prev_games.append(match.mother.pk)
        update_bracket(match.mother)
    

def update_brackets(parent_node, match, depth):
    global id_array
    father_dict = {}
    mother_dict = {}
    my_dict = {}
    my_dict.update({"winner" : match.winner.name, 
                    "match_id" : str(match.pk),
                    "log_location" : get_best_gamelog(match),
                    "previous_matches" : [],
                    "player_1" : match.p0.name,
                    "player_2" : match.p1.name})

    parent_node.update(my_dict)
    id_array.update({match.pk : my_dict})
    
    if match.father and match.father.pk in id_array.keys():
        my_dict["previous_matches"].append(match.father.pk)
        return

    if match.father and match.father.pk not in id_array.keys():
        my_dict["previous_matches"].append(father_dict)
        update_brackets(father_dict, match.father, depth+1)
    
    if match.mother and match.mother.pk in id_array.keys():
        my_dict["previous_matches"].append(match.mother.pk)
        return

    if match.mother and match.mother.pk not in id_array.keys():
        my_dict["previous_matches"].append(mother_dict)
        update_brackets(mother_dict, match.mother, depth+1)

if __name__ == "__main__":
    main()
