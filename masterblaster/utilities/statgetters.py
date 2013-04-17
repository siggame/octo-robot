def fetch_stats(game_turns):
  k = list()

  pos_animations = ['spawn', 'move', 'pickUp', 'death', 'drop', 'attack']

  k.append(len(game_turns))
  k.append(total_deaths(game_turns))
  k.append(average_deaths(game_turns))
  #spce = all_species(game_turns)
  #for i in spce:
  #  k.append(i)

  k.append(win_changes(game_turns))

  #anim = all_animations(game_turns, pos_animations)
  #for i in anim:
  #  k.append(i)

  #k.append(lose_amount(game_turns))
  return k


def all_animations(game_turns, anim):
  num_list = [0 for _ in anim]
  for x in game_turns:
    for i in x.animation:
      if i.stats[0] in anim:
        num_list[anim.index(i.stats[0])] = num_list[anim.index(i.stats[0])] + 1

  return num_list


def all_species(game_turns):
  species_num = [0 for _ in xrange(12)]

  for x in game_turns:
    for i in x.animation:
      if i.stats[0] == 'spawn':
        species_num[i.stats[4]] = species_num[i.stats[4]] + 1

  return species_num


def win_changes(game_turns):
  current_lead = -1
  prev_lead = 0

  win_changes = 0

  for x in game_turns:
    prev_lead = current_lead
    if x.player[0].stats[3] > x.player[1].stats[3]:
      current_lead = 0
    elif x.player[0].stats[3] < x.player[1].stats[3]:
      current_lead = 1
    if prev_lead != current_lead:
      win_changes = win_changes + 1

  return win_changes


def total_deaths(game_turns):
  total_deaths = 0

  for x in game_turns:
    for i in x.animation:
      if i.stats[0] == 'death':
        total_deaths = total_deaths + 1
  return total_deaths


def average_deaths(game):
  k = total_deaths(game)

  return (float(k) / len(game))


def num_species(game_turns, species):
  num_s = 0
  for x in game_turns:
    for i in x.animation:
      if i.stats[0] == 'spawn' and i.stats[4] == species:
        num_s = num_s + 1
  return num_s
