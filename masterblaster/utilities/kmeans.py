from k_storage.models import DataPoint
from random import random

# returns a list of data points which represent clusters, each having a rating value
# also setups up the database for queries 
def generate_clusters(cluster_count):
    clusters = create_random_clusters(cluster_count, 10)
    
    


# deletes old clusters and creates new ones
def create_random_clusters(cluster_count, attribute_count):
    data = list(DataPoint.objects.all())
    for i in data:
        if not i.data_point:
            i.delete()

    clusters = [DataPoint(data_point=False, cluster_id=i) for i in range(cluster_count)]
    for i in clusters:
        i.attributes = [random() for i in range(attribute_count)]
        i.save()
    return clusters
