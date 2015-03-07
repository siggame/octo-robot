from k_storage.models import add_data_point, DataPoint
from thunderdome.models import Game

import random

# do note this will be very slow and take a lot of time
def update_all_data():
    pass

def create_fake_data():
    games = list(Game.objects.all())
    for i in games:
        add_data_point([random.randint(0, 100) for j in range(4)], 
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
    pass


if __name__ == "__main__":
    update_all_ratings()
    # create_fake_data()
