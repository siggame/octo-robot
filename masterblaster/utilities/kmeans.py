from k_storage.models import DataPoint
from random import random
from collections import defaultdict
import math

# returns a list of data points which represent clusters, each having a rating value
# also setups up the database for queries 
def generate_clusters(cluster_count, eplison):
    clusters = create_random_clusters(cluster_count, 10)
    
    assign_clusters(clusters)
    update_clusters(clusters)

# deletes old clusters and creates new ones
def create_random_clusters(cluster_count, attribute_count):
    data = list(DataPoint.objects.all())
    for i in data:
        if not i.data_point:
            i.delete()

    clusters = [DataPoint(data_point=False, cluster_id=i) for i in range(cluster_count)]
    print clusters
    for i in clusters:
        i.attributes = [random() for j in range(attribute_count)]
        i.save()
    return clusters

def assign_clusters(clusters):
    data = list(DataPoint.objects.filter(data_point=True))
    
    for i in data:
        min_dist = float('inf')
        for j in clusters:
            temp_d = man_hat(i, j)
            if temp_d < min_dist:
                min_dist = temp_d
                i.cluster_id = j.cluster_id
                i.save()

def update_clusters(clusters):
    centroids = compute_centroids()
    clusters = list(DataPoint.objects.filter(data_point=False))
    for i in clusters:
        i.attributes = centroids[i.cluster_id]
        i.save()

def compute_centroids():
    data = list(DataPoint.objects.filter(data_point=True))
    cluster_dict = defaultdict(list)
    for i in data:
        cluster_dict[i.cluster_id].append(i)
    centroids = {cluster_dict[i].cluster_id : compute_centroid(cluster_dict[i]) for i in cluster_dict.keys()}
    return centroids
    
def compute_centroid(data):
    if data:
        attributes = [0 for i in len(data.attributes)]
        for i in data:
            for index, j in enumerate(i.attributes):
                attributes[index] += j
        t_d = len(data)
        attributes = [i/t_d for i in attributes]
        return attributes

def man_hat(point1, point2):
    sum_t = 0
    for i, j in zip(point1.attributes, point2.attributes):
        sum_t += math.abs(i - j)
    return sum_t

if __name__ == "__main__":
    # generate_clusters(3, 1)
    create_random_clusters(2, 3)
