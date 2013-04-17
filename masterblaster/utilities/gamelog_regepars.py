import re
from collections import defaultdict
from collections import Counter

def num_win_changes(gamelog):
    pattern = "\"Player\" \([01] \"[^\"]+\" [\d\.]+ (\d+) \d+\) \([01] \"[^\"]+\" [\d\.]+ (\d+)"

    player_health = re.findall(pattern, gamelog)

    num_count = 0
    current_lead = 0
    prev_lead = current_lead

    for i, j in player_health:
        prev_lead = current_lead
        if int(i) < int(j):
            current_lead = 1
        elif int(i) > int(j):
            current_lead = -1
        if prev_lead != current_lead:
            num_count = num_count + 1

    return num_count


def num_species_all(gamelog):
    pattern = "\(\"spawn\" \d+ \d+ \d+ \"([^\"]+)\""

    stuff = re.findall(pattern, gamelog)

    sa = Counter(stuff)
    df = defaultdict()
    df.update(sa)
    return df


def get_stats(gamelog):
    k = list()
    species_list = ['Sea Star','Sponge', 'Angelfish', 'Coneshell Snail', 'Sea Urchin', 'Octopus', 'Tomcod', 'Reef Shark', 'Cuttlefish', 'Cleaner Shrimp', 'Electric Eel', 'Jellyfish']
    num_turns = gamelog.count('game')
    num_deaths = gamelog.count('death')

    k.append(num_turns)
    k.append(num_deaths)
    k.append((num_deaths / float(num_turns)))
    k.append(num_win_changes(gamelog))

    num_species = num_species_all(gamelog)

    for i in species_list:
        try:
            k.append(num_species[i])
        except:
            k.append(0)

    k.append(gamelog.count('spawn'))
    k.append(gamelog.count('move'))
    k.append(gamelog.count('pickUp'))
    k.append(gamelog.count('drop'))
    k.append(gamelog.count('attack'))

    return k
