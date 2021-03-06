from django.db import models
import json



# Create your models here.
class DataPoint(models.Model):
    cluster_id = models.IntegerField(default=-1)

    # indicates wether or not the data point is a cluster value or an actual data point
    data_point = models.BooleanField(default=True)
    rating_value = models.FloatField(default=0.0)
    game_id = models.IntegerField(default=-1) # if game_id equals -1 then it must also be a cluster point
    _attributes = models.TextField(default='')
    
    @property
    def attributes(self):
        return json.loads(self._attributes)

    @attributes.setter
    def attributes(self, data):
        self._attributes = json.dumps(data)


# Helper functions
def add_cluster_point(initial_data, cluster_id):
    DataPoint(attributes=initial_data, 
              cluster_id=cluster_id, data_point=False).save()

# game_id is the corresponding pk_id of the Game models
# if a data point doesn't exist, it will then create one
# else it will update the datapoint
def update_data_point(data, game_id, cluster_id=-1):
    dp, created = DataPoint.objects.get_or_create(game_id=game_id)
    if created:
        dp.attributes=data
        dp.cluster_id=cluster_id
        dp.data_point=True
    else:
        dp.attributes=data
        dp.cluster_id=cluster_id
    dp.save()

def data_by_cluster_id(cluster_id):
    data_points = list(DataPoint.objects.filter(cluster_id=cluster_id))
    return [i.attributes for i in data_points]

