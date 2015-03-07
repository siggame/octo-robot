from k_storage.models import add_data_point, DataPoint
from thunderdome.models import Game




def update_all_data():
    pass

def update_all_ratings():
    games = list(Game.objects.all()):
    for i in games:
        try:
            print "getting data point", i.pk
            data_point = DataPoint.objects.get(game_id=i.pk)
            data_point.rating_value = i.get_average_rating()
            data_point.save()
        except:
            continue

    pass

def add_gamelog_data(gameObject):
    pass


if __name__ == "__main__":
    update_all_ratings()
