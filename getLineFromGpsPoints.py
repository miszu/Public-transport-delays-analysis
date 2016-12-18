import folium
import pandas as pd, numpy as np, matplotlib.pyplot as plt
import random
from numpy import sin,cos,arctan2,sqrt,pi
from shapely.geometry import MultiPoint
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle

####################################
## functions below are taken (and modified a bit) from blog post published by Geoff Boeing
## http://geoffboeing.com/2014/08/clustering-to-reduce-spatial-data-set-size/
####################################

def getDbScanClustersCenters(df, epsInKm, minObjects):
    clusters = getDbScanClusters(df, epsInKm, minObjects)
    return getClustersCenters(clusters)
    
def getDbScanClusters(df, epsInKm, minObjects):
    coords = df.as_matrix()
    kms_per_radian = 6371.0088
    epsilon = epsInKm / kms_per_radian
    db = DBSCAN(eps=epsilon, min_samples=minObjects, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
    cluster_labels = db.labels_
    print('Number of clusters: {}'.format(len(set(cluster_labels))))
    return pd.Series([coords[cluster_labels == n] for n in range(len(set(cluster_labels)) - 1)])

def get_centermost_point(cluster):
    centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)
    centermost_point = min(cluster, key=lambda point: great_circle(point, centroid).m)
    return centermost_point

def getClustersCenters(clusters):
    centermost_points = clusters.map(get_centermost_point)
    lats, lons = zip(*centermost_points)
    return pd.DataFrame({'lon':lons, 'lat':lats}).values.tolist()

####################################

def drawPointsOnMap(superMap, points, color, radiusSize):
    print('Drawing {} points on map'.format(len(points)))
    for point in points:
        folium.CircleMarker(point, radius = radiusSize, fill_color = color, color = color).add_to(superMap)
        
def getDistanceBetweenPoints(point1, point2):
        lon1 = point1[1] * pi / 180.0
        lon2 = point2[1] * pi / 180.0
        lat1 = point1[0] * pi / 180.0
        lat2 = point2[0] * pi / 180.0
        
        # haversine formula #### Same, but atan2 named arctan2 in numpy
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = (sin(dlat/2))**2 + cos(lat1) * cos(lat2) * (sin(dlon/2.0))**2
        c = 2.0 * arctan2(sqrt(a), sqrt(1.0-a))
        km = 6371.0 * c
        return km
    
def getEndPoint(points):
    pointsForFindingLineEnd = list(points)
    currentPoint = random.choice(pointsForFindingLineEnd)

    pointsForFindingLineEnd.remove(currentPoint)

    while(len(pointsForFindingLineEnd) > 0):
        nextPoint = None
        distanceToNextPoint = float("inf")
        for point in pointsForFindingLineEnd:
            distance = getDistanceBetweenPoints(point, currentPoint)
            if (distance < distanceToNextPoint):
                nextPoint = point
                distanceToNextPoint= distance
    
        pointsForFindingLineEnd.remove(nextPoint)
        currentPoint = nextPoint
    
    return currentPoint

def getLineFromPoints(points, startingPoint):
    linePoints = list(points)
    currentPoint = startingPoint
    line = []
    while(len(linePoints) > 0):
        nextPoint = None
        distanceToNextPoint = float("inf")
        for point in linePoints:
            distance = getDistanceBetweenPoints(point,currentPoint)
            if (distance < distanceToNextPoint):
                nextPoint = point
                distanceToNextPoint= distance

        linePoints.remove(nextPoint)
        currentPoint = nextPoint
        line.append(currentPoint)

    return line
        
df = pd.read_csv('locations.csv', index_col = False, header=0)
superMap = folium.Map(location=[51.107885, 17.038538], zoom_start=14, tiles='OpenStreetMap')
drawPointsOnMap(superMap, df.values, '#3186cc', 20)
    
clustersCenters = getDbScanClustersCenters(df, 0.03, 10)
drawPointsOnMap(superMap, clustersCenters, '#ff0000', 30)

endPoint = getEndPoint(clustersCenters)
drawPointsOnMap(superMap, [endPoint], '#ff0000', 100)
line = getLineFromPoints(clustersCenters, endPoint)

superMap.add_children(folium.PolyLine(locations = line, weight = 10, color="#d63b3b"))

superMap.save('map.html')