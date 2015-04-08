from k_storage.models import update_data_point, DataPoint
from thunderdome.models import Game

from glogdata.file_manip import create_from_url

import random

# do note this will be very slow and can take a lot of time
def update_all_data():
    games = list(Game.objects.filter(status='Complete'))
    for i in games:
        add_gamelog_data(i)

def update_data_range(min_id, max_id):
    games = list(Game.objects.filter(pk__gte=min_id).filter(pk__lte=max_id))
    for i in games:
        add_gamelog_data(i)

def clear_all_data():
    data = list(DataPoint.objects.all())
    for i in data:
        i.delete()

def create_fake_data():
    games = list(Game.objects.all())
    for i in games:
        update_data_point([random.randint(0, 100) for j in range(4)], 
                       i.pk)

def update_all_ratings():
    games = list(Game.objects.all())
    for i in games:
        try:
            print "getting data point", i.pk
            data_point = DataPoint.objects.get(game_id=i.pk)
            data_point.rating_value = i.get_average_rating()
            data_point.save()
        except:
            continue

# adds an data point to the provided game data object, should be of type Game
# if the gamelog url is not a proper location such as '' then will not add a data point to the database
def add_gamelog_data(gamedata):
    if gamedata.gamelog_url:
        print "Adding data point for game", gamedata.pk
        gamelog_data = create_from_url(gamedata.gamelog_url)
        update_data_point(gamelog_data.attributes(), gamedata.pk)

if __name__ == "__main__":
    update_all_data()
    
