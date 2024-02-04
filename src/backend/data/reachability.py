import polyline
import requests
import pandas as pd
import os
import flexpolyline as fp
from geopy.distance import geodesic
from dateutil import parser
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import numpy as np
from dateutil.parser import parse
from tqdm import tqdm

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


def generate_periods(start_date, end_date, duration):
    start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
    start_dates = pd.date_range(start_date, end_date, freq=f'{duration}D')

    periods = []
    for i, start in enumerate(start_dates):
        end = start + timedelta(days=duration-1)
        if end > end_date:
            end = end_date
        periods.append((start, end))

    return periods


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


def convert_to_minutes(time_str):
    time_parts = time_str.split()
    total_minutes = 0
    for part in time_parts:
        if 'd' in part:
            total_minutes += int(part.replace('d', '')) * 60 * 24
        elif 'h' in part:
            total_minutes += int(part.replace('h', '')) * 60
        elif 'm' in part:
            total_minutes += int(part.replace('m', ''))
    return total_minutes


def getLocationJSON(loc_name, country_name):
    """
    Returns unique Kayak location identifier for a given location
    args:
        loc_name: The name of the location
    returns:
        The JSON response of the request
    """

    url = "https://www.kayak.com/mvm/smartyv2/search"

    querystring = {
        "f":"j",
        "s":"50",
        "where":f"{loc_name}, {country_name}",
        "sv":"",
        "cv":"undefined",
        "c":"undefined",
                }

    payload = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Accept": "*/*",
        "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.kayak.de",
        "DNT": "1",
        "Sec-GPC": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Content-Length": "0",
        "TE": "trailers"
    }

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    if response.status_code == 429:
        print("Too many requests. Waiting for 3 minutes...")
        time.sleep(180)
        return getLocationJSON(loc_name, country_name)

    return response.json()


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
                    "route": 0,
                    "distance": 0,
                    'total_transfers': 0
                }

            else:
                poly_line = poly_coord_dict['polyline']
                route_coords = poly_coord_dict['coords']

                departure = parse(json_r['routes'][0]['sections'][0]['departure']['time'])
                arrival = parse(json_r['routes'][0]['sections'][-1]['arrival']['time'])

                # compute time difference between departure and arrival
                total_seconds = (arrival - departure).total_seconds()

                return {
                    "start_point": route_coords[0],
                    "end_point": route_coords[-1],
                    "duration": total_seconds,
                    "polyline": poly_line,
                    "route": route_coords,
                    "distance": calculate_total_distance(route_coords),
                    'total_transfers': countNonPedestrianRoutes(json_r)
                }

        else:
            return {}
        

    def createFlightSearchURL(self, orig_iata: str, dest_iata: str, date_leave: str) -> str:

        date_ret_ts = datetime.strptime(date_leave, "%Y-%m-%d") + timedelta(days=7)
        date_ret = date_ret_ts.strftime("%Y-%m-%d")

        url = f"https://www.kayak.com/flights/{orig_iata}-{dest_iata}/{date_leave}/{date_ret}?sort=bestflight_a"
        return url
    

    def getFlightData(self, orig, dest, date_leave):

        url = self.createFlightSearchURL(orig, dest, date_leave)

        # FIXME: 404 page not found and Belarus

        # set up selenium
        options = webdriver.ChromeOptions()
        #options.add_argument('--headless')
        options.add_argument('--no-sandbox')

        driver = webdriver.Chrome(options=options)

        try:

            # wait for presence of the x / y results element
            max_wait = 40
            driver.get(url)
            WebDriverWait(driver, max_wait).until(EC.presence_of_element_located((By.CLASS_NAME, "nrc6")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()

        except:
            driver.quit()
            return None

        return soup
        

    def parseFlightData(self, orig, dest, date_leave, soup):
        """

        """

        flight_data = {
                'origin': orig,
                'destination': dest,
                'date_leave': pd.to_datetime(date_leave),
                'duration': [],
                'stops': [],
                'time': [],
                'price': [],
                'full_desc': [],
            }

        try:

            for nrc6_element in soup.select('.nrc6-inner'):
                vmXl_elements = nrc6_element.select('.vmXl-mod-variant-default')
                flight_data['stops'].append(vmXl_elements[0].text)
                flight_data['duration'].append(vmXl_elements[1].text)
                flight_data['time'].append(nrc6_element.select('.vmXl-mod-variant-large')[0].text)
                flight_data['price'].append(int(nrc6_element.select('.f8F1-price-text')[0].text[1:].replace(',', '')))
                flight_data['full_desc'].append(nrc6_element.text)

            flight_data['stops'] = [0 if stop == "nonstop" else int(stop.split(" ")[0]) for stop in flight_data['stops']]
            flight_data['duration'] = [convert_to_minutes(dur) for dur in flight_data['duration']]

            return {
                "orig_iata": orig, "dest_iata": dest,
                "total_flights": len(flight_data['price']), "dep_date": flight_data['date_leave'].strftime('%Y-%m-%d'),
                "avg_price": sum(flight_data['price']) / len(flight_data['price']),
                "min_price": min(flight_data['price']), "max_price": max(flight_data['price']),
                "avg_duration": sum(flight_data['duration']) / len(flight_data['duration']),
                "min_duration": min(flight_data['duration']), "max_duration": max(flight_data['duration']),
                "avg_stops": sum(flight_data['stops']) / len(flight_data['stops'])
                }

        except:
            print(f"Error parsing flight data for {orig} to {dest} on {date_leave}")
            return None
        

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
        tmp_dict = {
            'loc_id': loc['location_id'],
            'ref_id': row['location_id'],
            'arr_city': loc['city'],
            'dep_city': row['city']
                }

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
                tmp_dict['pt_distance'] = 0
                tmp_dict['pt_duration'] = 0
                tmp_dict['pt_polyline'] = None
                tmp_dict['pt_total_transfers'] = 0

        else:
            tmp_dict['car_distance'] = 0
            tmp_dict['car_duration'] = 0
            tmp_dict['car_polyline'] = None
            tmp_dict['pt_distance'] = 0
            tmp_dict['pt_duration'] = 0
            tmp_dict['pt_polyline'] = None
            tmp_dict['pt_total_transfers'] = 0
        
        # return dataframe of results to be inserted into database
        res.append(pd.DataFrame(tmp_dict, index=[0]))

    return pd.concat(res)
    

def process_location_air_reachability(loc: pd.DataFrame, start_refs: pd.DataFrame, processed_locs) -> pd.DataFrame:
    """
    Processes the air reachability of a given location airport and a set of reference airports.
    Args:
        loc (pd.DataFrame): The location airport.
        start_refs (pd.DataFrame): The reference airports.
    Returns:
        pd.DataFrame: The air reachability data.
    """

    # set periods manually: each day of the week one time per season (winter summer); Febrary and March twice (2024 and 2025) because they are closest to the start date
    start_dates = [
        "2024-02-26", "2024-03-05", "2024-04-17", "2024-05-23", "2024-06-28",
        "2024-07-06", "2024-08-11", "2024-09-16", "2024-10-29", "2024-11-06", 
        "2024-12-12", "2025-01-17", "2025-02-22", "2025-03-02"
    ]

    # create destination coordinate dict for Route object constructor
    dest = {
        "lat": float(loc['lat']),
        "lon": float(loc['lon'])
    }

    dest_iata = loc['airport_1']
    res_list = []

    # loop over all periods and reference airports
    for dep_date in start_dates:

        for _, row in start_refs.iterrows():

            orig_iata = row['mapped_start_airport']

            # check if flight data for this route and date has already been processed
            if processed_locs is not None:
                if len(processed_locs[(processed_locs['orig_iata'] == orig_iata & processed_locs['dest_iata'] == dest_iata & processed_locs['dep_date'] == dep_date)]) > 0:
                    continue

            #time.sleep(5)

            # specify origin coordinates for Route object constructor
            orig = {
                "lat": float(row['lat']),
                "lon": float(row['lon'])
            }

            # set origin iata code, create Route object
            route = Route(dest, orig)

            # get flight data
            soup = route.getFlightData(orig_iata, dest_iata, dep_date)
            print(f"Kayak page fetched successfully for {orig_iata} to {dest_iata} on {dep_date}")
            try:
                flight_data = route.parseFlightData(orig_iata, dest_iata, dep_date, soup)
                print(f"Flight data parsed successfully for {orig_iata} to {dest_iata} on {dep_date}")

                # insert flight data into database
                if flight_data is not None:
                    flight_data['orig_iata'] = orig_iata
                    flight_data['dest_iata'] = dest_iata
                    res_list.append(pd.DataFrame(flight_data, index=[0]))
                    print(f"SUCCESS: data found for {orig_iata} to {loc['city']} on {dep_date}")
                    continue

            except:
                pass

            print(f"WARNING: No flight data found for {orig_iata} to {loc['city']} on {dep_date}")
                        
     # after iterating through time periods and locations, return the dataframe                   
    return pd.concat(res_list)
