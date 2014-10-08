
from thunderdome.models import Match
from pprint import pprint
import random

loop = 0

def main():
    tournament_id = 20133422
    championship = Match.objects.get(root=True, tournament=tournament_id)

    k = {}
    update_brackets(k, championship, 0)
    
    pprint(k)
    #pprint(id_array)

def get_best_gamelog(match):
    games = list(match.games.all())
    if games:
        return random.choice(games).gamelog_url
    else:
        return ''


id_array = {}

from copy import deepcopy

def update_brackets(parent_node, match, depth):
    global loop
    global id_array
    father_dict = {}
    mother_dict = {}
    my_dict = {}
    my_dict.update({match.pk : {'gamelog' : get_best_gamelog(match),
                                'prev_games' : [father_dict, mother_dict]}})
    loop += 1
    parent_node.update(my_dict)
    print loop, depth, match.pk

    id_array.update({match.pk : my_dict})
    
    if match.father and match.father.pk in id_array.keys():
        my_dict[match.pk]['prev_games'][0] = id_array[match.father.pk]
        return

    if match.father and match.father.pk not in id_array.keys():
        update_brackets(father_dict, match.father, depth+1)
    
    if match.mother and match.mother.pk in id_array.keys():
        my_dict[match.pk]['prev_games'][1] = id_array[match.mother.pk]
        return

    if match.mother and match.mother.pk not in id_array.keys():
        update_brackets(mother_dict, match.mother, depth+1)

if __name__ == "__main__":
    main()
