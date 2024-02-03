import folium
import polyline
import requests
import pandas as pd
import sys
import os
import flexpolyline as fp
from geopy.distance import geodesic
from dateutil import parser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dateutil import parser

with open("./res/auth/here_key.txt", "r") as f:
    key = f.read()

# set key to environment variable
os.environ["HERE_API_KEY"] = key


# helper functions
def calculate_total_distance(coords):
    total_distance = 0
    for i in range(len(coords) - 1):
        total_distance += geodesic(coords[i], coords[i+1]).meters
    return total_distance


def countNonPedestrianRoutes(route):

    if len(route['routes']) == 0:
        return 0
    
    count = 0
    for section in route['routes'][0]['sections']:
        if section['transport']['mode'] != "pedestrian":
            count += 1
    return count


def computeTotalTime(route) -> float:
    """
    Computes the time difference between the departure time at the origin and the arrival time at the destination.
    Args:
        route (dict): The route dictionary returned by the HERE API.
    Returns:
        datetime.timedelta: The time difference between the departure time at the origin and the arrival time at the destination.
    """

    assert route is not None

    if len(route['routes']) == 0:
        return {}

    start = parser.parse(route['routes'][0]['sections'][0]['departure']['time'])
    end = parser.parse(route['routes'][0]['sections'][-1]['arrival']['time'])

    return end - start


def getTotalRouteCoords(route) -> str:

    assert route is not None

    if len(route['routes']) == 0:
        return {}

    coords = []

    for section in route['routes'][0]['sections']:
        coords.extend(fp.decode(section['polyline']))

    # Re-encode the total route coordinates into a polyline string
    total_route_polyline = fp.encode(coords)

    return {"polyline": total_route_polyline, "coords": coords}


class Route:

    def __init__(self, dest: dict, orig: dict):
        self.dest = dest
        self.orig = orig


    def get_car_route(self):

        start = "{},{}".format(self.orig['lon'], self.orig['lat'])
        end = "{},{}".format(self.dest['lon'], self.dest['lat'])
        
        url = 'http://router.project-osrm.org/route/v1/driving/{};{}?alternatives=false&annotations=nodes'.format(start, end)
        r = requests.get(url) 
        if r.status_code!= 200:
            return {}
        
        res = r.json()   
        routes = polyline.decode(res['routes'][0]['geometry'])
        start_point = (res['waypoints'][0]['location'][1], res['waypoints'][0]['location'][0])
        end_point = (res['waypoints'][1]['location'][1], res['waypoints'][1]['location'][0])
        distance = res['routes'][0]['distance']
        duration = res['routes'][0]['duration']
        
        out = {
            'route': routes,
            'start_point': {'lat': start_point[0], 'lon': start_point[1]},
            'end_point': {'lat': end_point[0], 'lon': end_point[1]},
            'distance': distance,
            'duration': duration,
            'polyline': res['routes'][0]['geometry']
            }

        return out
    

    def car_route_available(self):

        if self.get_car_route() == {}:
            return False

        else:

            car_route = self.get_car_route()
            return ((self.dest['lon'] - car_route['end_point']['lon'] <= 0.1) and 
                    (self.dest['lat'] - car_route['end_point']['lat'] <= 0.1))
        

    def get_public_transport_route(self, orig, dest, key, max_distance="2000"):

        params = {
            "apiKey": key,
            "origin": str(orig['lat']) + "," + str(orig['lon']),
            "destination": str(dest['lat']) + "," + str(dest['lon']),
            "pedestrian[maxDistance]": max_distance,
            "return": "polyline,intermediate,fares,bookingLinks,travelSummary"
        }

        r = requests.get('https://transit.router.hereapi.com/v8/routes', params=params)

        if r.status_code == 200:

            json_r = r.json()

            poly_coord_dict = getTotalRouteCoords(json_r)

            if poly_coord_dict == {}:
                return {
                    "start_point": None,
                    "end_point": None,
                    "duration": None,
                    "polyline": None,
                    "route": None,
                    "distance": None,
                    'total_transfers': None
                }

            else:
                poly_line = poly_coord_dict['polyline']
                route_coords = poly_coord_dict['coords']

                return {
                    "start_point": route_coords[0],
                    "end_point": route_coords[-1],
                    "duration": computeTotalTime(json_r),
                    "polyline": poly_line,
                    "route": route_coords,
                    "distance": calculate_total_distance(route_coords),
                    'total_transfers': countNonPedestrianRoutes(json_r)
                }

        else:
            return {}
        

def process_location_land_reachability(loc, start_refs):

    res, counter = [], 0

    key = os.environ.get("HERE_API_KEY")

    for _, row in start_refs.iterrows():

        print(f"Processing location {loc['city']} with reference {row['city']}...")

        orig = {
            "lat": float(row['lat']),
            "lon": float(row['lon'])
        }

        dest = {
            "lat": float(loc['lat']),
            "lon": float(loc['lon'])
        }

        route = Route(dest, orig)
        tmp_dict = {}

        # car route
        if route.car_route_available():
            car_route = route.get_car_route()
            #print("car route available")
            tmp_dict['car_distance'] = car_route['distance']
            tmp_dict['car_duration'] = car_route['duration']
            tmp_dict['car_polyline'] = car_route['polyline']

            # public transport route
            if car_route['duration'] < 3600*20:
                print("public transport route available")
                pt_route = route.get_public_transport_route(orig, dest, key)
                tmp_dict['pt_distance'] = pt_route['distance']
                tmp_dict['pt_duration'] = pt_route['duration']
                tmp_dict['pt_polyline'] = pt_route['polyline']
                tmp_dict['pt_total_transfers'] = pt_route['total_transfers']

                counter +=1

                if counter >= 1000:
                    print("Reached maximum number of requests.")
                    break

            else:
                print("public transport route not available")
                tmp_dict['pt_distance'] = None
                tmp_dict['pt_duration'] = None
                tmp_dict['pt_polyline'] = None
                tmp_dict['pt_total_transfers'] = None

        else:
            tmp_dict['car_distance'] = None
            tmp_dict['car_duration'] = None
            tmp_dict['car_polyline'] = None
            tmp_dict['pt_distance'] = None
            tmp_dict['pt_duration'] = None
            tmp_dict['pt_polyline'] = None
            tmp_dict['pt_total_transfers'] = None
        
        # return dataframe of results to be inserted into database
        res.append(pd.DataFrame(tmp_dict, index=[0]))

    return pd.concat(res)
    

def process_location_air_reachability():

    pass