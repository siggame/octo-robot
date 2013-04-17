from math import pi, sin, cos
from collections import namedtuple
from random import random, choice, randint
from copy import copy

import json

FLOAT_MAX = 1e100


class Point:
    """
    Point used to store data and its features,

    list features: x1, x2, x3, etc

    int group: the cluster that the point is associated with
    """

    def __init__(self, feature_list=[], group=0):
        self.num_features = 0
        self.set_features(feature_list)
        self.group = group
        self.rating = 0

    def __getitem__(self, i):
        return self.feature[i]

    def __setitem__(self, i, k):
        self.feature[i] = k

    def set_rating(self, i):
        self.rating = i

    def set_features(self, in_list):
        self.feature = copy(in_list)
        self.num_features = len(self.feature)

    def p_print(self):
        print "Group:", self.group, " ", self.feature

    def feature_string(self):
        st = ''
        for i in self.feature:
            st = st + ' ' + str(i)

        return st


def sqr_distance(a, b):
    """square distance of point a and b"""

    if a.num_features != b.num_features:
        print "ERROR: point a and point b have different len features"
        return 0

    dist = 0
    feature_list = zip(a.feature, b.feature)
    for i, j in feature_list:
        """i and j are the feature i of a and b
        just like
        Point2D x = new Point2D(1,2)
        1 = x[0] is equal to the x value
        2 = x[1] is equal to the y value
        """
        dist = dist + (i - j) ** 2
    return dist


def nearest_cluster_center(point, cluster_centers):
    """Distance and index of the closest cluster center"""

    min_index = point.group
    min_dist = FLOAT_MAX
    rating = -1

    for i, cc in enumerate(cluster_centers):
        d = sqr_distance(cc, point)
        if min_dist > d:
            min_dist = d
            min_index = i
            rating = cc.rating

    return (min_index, min_dist, rating)


def random_init(points, cluster_centers):

    max_point = Point(points[0].feature)

    for cc in cluster_centers:
        cc.set_features(max_point.feature)

    for i in points:
        for j in xrange(max_point.num_features):
            if max_point[j] < i[j]:
                max_point[j] = i[j]

    for cc in cluster_centers:
        for j in xrange(max_point.num_features):
            cc[j] = random() * max_point[j]

    for p in points:
        p.group = nearest_cluster_center(p, cluster_centers)[0]


def lloyd(points, nclusters):
    cluster_centers = [Point() for _ in xrange(nclusters)]

    random_init(points, cluster_centers)

    lenpts10 = len(points) >> 10

    changed = 0
    while True:

        for cc in cluster_centers:
            for i in xrange(cc.num_features):
                cc[i] = 0
            cc.group = 0

        for p in points:
            """
            using cluster_centers.group to denote how many
            points are in that cluster_center
            """
            cluster_centers[p.group].group += 1
            for i in xrange(cluster_centers[p.group].num_features):
                cluster_centers[p.group][i] += p[i]

        for cc in cluster_centers:
            for i in xrange(cc.num_features):
                if cc.group == 0:
                    cc[i] = 0
                else:
                    cc[i] /= cc.group

        #display(points, cluster_centers, len(cluster_centers));

        changed = 0
        for p in points:
            min_i = nearest_cluster_center(p, cluster_centers)[0]
            if min_i != p.group:
                changed += 1
                p.group = min_i

        if changed <= lenpts10:
            break

    for i, cc in enumerate(cluster_centers):
        cc.group = i

    set_cluster_ratings(points, cluster_centers)
    return cluster_centers


def eval_point(point, cluster_centers):

    return nearest_cluster_center(point, cluster_centers)


def load_data(games):

    points = []

    for g in games:
        if g.status == 'Complete':
            stats = json.loads(g.stats)

            tempP = Point()

            try:
                templist = copy(stats['rating_stats'])
            except:
                continue

            tempP.set_features(templist)

            try:
                ratings = copy(stats['votes'])
            except:
                ratings = []

            if len(ratings) != 0:
                tempP.set_rating(sum(ratings) / len(ratings))
            else:
                tempP.set_rating(0)

            points.append(tempP)

    return points


def set_cluster_ratings(points, cluster_centers):

    sum_t = 0
    count = 0
    for j in cluster_centers:
        sum_t = 0
        count = 0
        for i in points:
            if j.group == i.group:
                sum_t = sum_t + i.rating
                count = count + 1

        if count == 0:
            j.set_rating(0)
        else:
            j.set_rating(float(sum_t) / count)


def convert_to_point(game):
    tempP = Point()
    try:
        data = json.loads(game.stats)
        ratings = data['rating_stats']
    except:
        ratings = []

    tempP.set_features(ratings)
    return tempP


def obtain_clusters(games, num_clusters=10):
    points = load_data(games)

    #how to determine number of clusters?!?!?!?
    cluster_centers = lloyd(points, num_clusters)

    return cluster_centers
