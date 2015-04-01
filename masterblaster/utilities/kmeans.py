from k_storage.models import DataPoint
from random import random, choice
from collections import defaultdict
import math

# returns a list of data points which represent clusters, each having a rating value
# also setups up the database for queries 
def generate_clusters(cluster_count, eplison):
    clusters = create_random_clusters(cluster_count, 2)
    for i in clusters:
        print i.attributes

    run_count = 10
    c = 0
    while c < run_count: 
        assign_clusters(clusters)
        update_clusters(clusters)
        clusters = list(DataPoint.objects.filter(data_point=False))
        print "After update"
        for i in sorted(clusters, key=lambda x : x.cluster_id):
            print i.attributes

        c += 1
        if c == run_count:
            cull_clusters()

# deletes old clusters and creates new ones
def create_random_clusters(cluster_count, attribute_count):
    data = list(DataPoint.objects.all())
    for i in data:
        if not i.data_point:
            i.delete()

    clusters = [DataPoint(data_point=False, cluster_id=i) for i in range(cluster_count)]
    data = list(DataPoint.objects.all())
    for i in clusters:
        i.attributes = choice(data).attributes
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
        try:
            i.attributes = centroids[i.cluster_id]
            i.save()
        except:
            pass

def compute_centroids():
    data = list(DataPoint.objects.filter(data_point=True))
    cluster_dict = defaultdict(list)
    for i in data:
        cluster_dict[i.cluster_id].append(i)
    centroids = {i : compute_centroid(cluster_dict[i]) for i in cluster_dict.keys()}
    return centroids
    
def compute_centroid(data):
    if data:
        attributes = [0 for i in range(len(data[0].attributes))]
        for i in data:
            for index, j in enumerate(i.attributes):
                attributes[index] += j
        t_d = len(data)
        attributes = [i/t_d for i in attributes]
        return attributes

def man_hat(point1, point2):
    sum_t = 0
    for i, j in zip(point1.attributes, point2.attributes):
        sum_t += abs(i - j)
    return sum_t

def eqlid_dist(point1, point2):
    sum_t = 0
    for i, j in zip(point1.attributes, point2.attributes):
        sum_t += math.pow(i - j, 2)
    return math.sqrt(sum_t)

def evaluate_clusters(clusters):
    pass

def cull_clusters():
    pass

def output_data():
    t = [i.attributes for i in list(DataPoint.objects.filter(data_point=True))]
    import json
    print json.dumps(t)

if __name__ == "__main__":
    k = int(math.sqrt(len(list(DataPoint.objects.filter(data_point=True)))/2))
    print "Cluster count", k
    generate_clusters(k, 1)
    #create_random_clusters(2, 1)
