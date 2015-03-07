from k_storage.models import update_data_point, DataPoint
from thunderdome.models import Game

from glogdata.file_manip import create_from_url

import random

# do note this will be very slow and can take a lot of time
def update_all_data():
    games = list(Game.objects.all())
    for i in games:
        add_gamelog_data(i)

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

def add_gamelog_data(gamedata):
    if gamedata.gamelog_url:
        gamelog_data = create_from_url(gamedata.gamelog_url)
        #print gamelog_data.attributes()
        update_data_point(gamelog_data.attributes(), gamedata.pk)

if __name__ == "__main__":
    update_all_data()

