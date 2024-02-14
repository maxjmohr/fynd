import polyline
import requests
import pandas as pd
import os
import random
import time
from tqdm import tqdm
import flexpolyline as fp
from geopy.distance import geodesic
from dateutil import parser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil.parser import parse
from database.db_helpers import Database
from urllib3.exceptions import MaxRetryError
import numpy as np
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from dateutil import parser

with open("./res/auth/here_key.txt", "r") as f:
    key = f.read()

# set key to environment variable
os.environ["HERE_API_KEY"] = key

RANDOM_SLEEP_MIN = 0
RANDOM_SLEEP_MAX = 3
CAPTCHA_WAIT_TIME = 30
MAX_WAIT_TIME = 300
CAPTCHA_DETECTED = -1
NO_RESULTS_FOUND = 0


def generate_periods(start_date: str, end_date: str, duration: int) -> list:
    """
    Generates a list of periods of a given duration between two dates.
    """
    start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
    start_dates = pd.date_range(start_date, end_date, freq=f'{duration}D')

    periods = []
    for i, start in enumerate(start_dates):
        end = start + timedelta(days=duration-1)
        if end > end_date:
            end = end_date
        periods.append((start, end))

    return periods


def configureChromeDriver(headless: bool =False) -> webdriver.ChromeOptions:
    """
    Configures the Chrome driver options.
    """

    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1280,720')
    if headless: options.add_argument('--headless')

    return options


def calculate_total_distance(coords: list) -> float:
    """
    Calculates the total distance of a route given its coordinates.
    """
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


def computeTotalTime(route: dict) -> float:
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


def getTotalRouteCoords(route: dict) -> str:
    """
    Returns the total route coordinates as a polyline string.
    """

    assert route is not None

    if len(route['routes']) == 0:
        return {}

    coords = []

    for section in route['routes'][0]['sections']:
        coords.extend(fp.decode(section['polyline']))

    # Re-encode the total route coordinates into a polyline string
    total_route_polyline = fp.encode(coords)

    return {"polyline": total_route_polyline, "coords": coords}


def convert_to_minutes(time_str: str) -> int:
    """
    Converts a time string to minutes.
    """
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


class Route:
    """
    Class for route computation and reachability analysis.
    """

    def __init__(self, dest: dict, orig: dict):
        self.dest = dest
        self.orig = orig


    def get_car_route(self):
        """
        Returns the car route from the origin to the destination.
        """

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

        # Reverse the coordinates for GeoJSON (lon, lat instead of lat, lon)
        geojson_coords = [(lon, lat) for lat, lon in routes]
        geojson_dict = {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "LineString",
                "coordinates": geojson_coords
            }
        }
        
        out = {
            'route': routes,
            'start_point': {'lat': start_point[0], 'lon': start_point[1]},
            'end_point': {'lat': end_point[0], 'lon': end_point[1]},
            'distance': distance,
            'duration': duration / 60, # convert to minutes
            'geojson': json.dumps(geojson_dict),
            'polyline': res['routes'][0]['geometry']
            }

        return out
    

    def car_route_available(self):
        """
        Returns True if a car route is available, False otherwise.
        """

        if self.get_car_route() == {}:
            return False

        else:
            car_route = self.get_car_route()
            return ((np.abs(self.dest['lon'] - car_route['end_point']['lon']) <= 0.1) and 
                    (np.abs(self.dest['lat'] - car_route['end_point']['lat']) <= 0.1))
        

    def get_public_transport_route(self, key: str, max_distance: str ="2000") -> dict:
        """
        Returns the public transport route from the origin to the destination via the HERE API.
        """

        params = {
            "apiKey": key,
            "origin": str(self.orig['lat']) + "," + str(self.orig['lon']),
            "destination": str(self.dest['lat']) + "," + str(self.dest['lon']),
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
                    "geojson": None,
                    "polyline": None,
                    "route": 0,
                    "distance": 0,
                    'total_transfers': 0
                }

            else:
                poly_line = poly_coord_dict['polyline']
                route_coords = poly_coord_dict['coords']

                # Reverse the coordinates for GeoJSON (lon, lat instead of lat, lon)
                geojson_coords = [(lon, lat) for lat, lon in route_coords]
                geojson_dict = {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": geojson_coords
                    }
                }

                departure = parse(json_r['routes'][0]['sections'][0]['departure']['time'])
                arrival = parse(json_r['routes'][0]['sections'][-1]['arrival']['time'])

                # compute time difference between departure and arrival, convert to minutes
                total_minutes = (arrival - departure).total_seconds() / 60

                return {
                    "start_point": route_coords[0],
                    "end_point": route_coords[-1],
                    "duration": total_minutes,
                    "geojson": json.dumps(geojson_dict),
                    "route": route_coords,
                    "distance": calculate_total_distance(route_coords),
                    'total_transfers': countNonPedestrianRoutes(json_r),
                    'polyline': poly_line
                }

        else:
            return {}
        

    def createFlightSearchURL(self, orig_iata: str, dest_iata: str, date_leave: str) -> str:
        """
        Creates a flight search URL for a given origin, destination and departure date.
        Args:
            orig_iata (str): The IATA code of the origin airport.
            dest_iata (str): The IATA code of the destination airport.
            date_leave (str): The departure date.

        Returns:
            str: The flight search URL.
        """

        date_ret_ts = datetime.strptime(date_leave, "%Y-%m-%d") + timedelta(days=7)
        date_ret = date_ret_ts.strftime("%Y-%m-%d")

        url = f"https://www.kayak.com/flights/{orig_iata}-{dest_iata}/{date_leave}/{date_ret}"
        return url
    

    def getFlightData(self, driver: webdriver.Chrome, orig_iata: str, dest_iata: str, date_leave: str) -> BeautifulSoup:
        """
        Scrapes flight data from the Kayak website.
        Args:
            driver (webdriver.Chrome): The Chrome driver.
            orig_iata (str): The IATA code of the origin airport.
            dest_iata (str): The IATA code of the destination airport.
            date_leave (str): The departure date.
        Returns:
            BeautifulSoup: The parsed HTML of the Kayak website.
        """

        # sleep random amount between 0 and 3 seconds
        sleep_time = random.uniform(RANDOM_SLEEP_MIN, RANDOM_SLEEP_MAX)
        time.sleep(sleep_time)
        url = self.createFlightSearchURL(orig_iata, dest_iata, date_leave)
        driver.get(url)

        try:
            # wait for presence of the x / y results element
            WebDriverWait(driver, MAX_WAIT_TIME).until(EC.presence_of_element_located((By.CLASS_NAME, "nrc6")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            return soup
        
        except TimeoutException as e:
            print("Getting flight results page timed out.")
            pass
        
        # check for captcha
        try:
            element_text = "Please confirm that you are a real KAYAK user."
            error_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{element_text}')]")
            #error_element = WebDriverWait(driver, CAPTCHA_WAIT_TIME).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{element_text}')]")))
            print("Captcha detected.")
            return CAPTCHA_DETECTED

        except NoSuchElementException as e:
            print("Captcha detection timed out")
            pass

        # Kayak restricts access to certain countries (Russia, Belarus, Iran)
        try:
            element_text = "Due to government restrictions, we are unable to show results for this search."
            error_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{element_text}')]")
            #error_element = WebDriverWait(driver, CAPTCHA_WAIT_TIME).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{element_text}')]")))
            return NO_RESULTS_FOUND
        
        except NoSuchElementException as e:
            print("Government restriction detection timed out")
            pass

        # if "No flight founds" element pops up, return -1
        try:
            element_text = f"No matching flights found between {orig_iata} and {dest_iata} for these dates."
            driver.find_element(By.XPATH, f"//*[contains(text(), '{element_text}')]")
            print(f"No flights available for {orig_iata} to {dest_iata} on {date_leave}.")
            return NO_RESULTS_FOUND

        except NoSuchElementException as e:
            print(f"Looking for empty connection element for {dest_iata} to {orig_iata} timed out.")
            return None
        

    def parseFlightData(self, orig_iata: str, dest_iata: str, date_leave: str, soup: BeautifulSoup):
        """
        Parses soup returned by getFlightData method.
        Args:
            orig_iata (str): The IATA code of the origin airport.
            dest_iata (str): The IATA code of the destination airport.
            date_leave (str): The departure date.
            soup (BeautifulSoup): The parsed HTML of the Kayak website.
        Returns:
            dict: The parsed flight data.
        """
        
        if soup == 0:
            return {
                "orig_iata": orig_iata, "dest_iata": dest_iata,
                "total_flights": 0, "dep_date": date_leave,
                "avg_price": None, "min_price": None, "max_price": None,
                "avg_duration": None, "min_duration": None, "max_duration": None,
                "avg_stops": None
            }

        elif soup == -1:
            return -1
        
        elif soup is not None:
            flight_data = {
                'origin': orig_iata,
                'destination': dest_iata,
                'date_leave': pd.to_datetime(date_leave),
                'duration': [],
                'stops': [],
                'time': [],
                'price': [],
                'full_desc': [],
            }

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
                "orig_iata": orig_iata, "dest_iata": dest_iata,
                "total_flights": len(flight_data['price']), "dep_date": flight_data['date_leave'].strftime('%Y-%m-%d'),
                "avg_price": sum(flight_data['price']) / len(flight_data['price']),
                "min_price": min(flight_data['price']), "max_price": max(flight_data['price']),
                "avg_duration": sum(flight_data['duration']) / len(flight_data['duration']),
                "min_duration": min(flight_data['duration']), "max_duration": max(flight_data['duration']),
                "avg_stops": sum(flight_data['stops']) / len(flight_data['stops'])
                }
        
        else:
            return None
    

def fill_reachibility_table(locations: pd.DataFrame, 
                            start_refs: pd.DataFrame, 
                            processed_locs: pd.DataFrame,
                            periods: list,
                            mode: str = "land"):
    """
    Fills the reachability tables with default data on which the scores are computed.
    Args:
        locs (pd.DataFrame): The (core) locations for which the reachability is computed.
        start_refs (pd.DataFrame): The reference locations for the reachability computation.
        processed_locs (pd.DataFrame): The processed rows for which no further computation is necessary.
        periods (list): The periods for which the reachability is computed.
        mode (str): The mode of reachability computation.
    Returns:
        None
    """

    insert_data = []

    if mode == "land":

        # inititalize empty dictionary with default values
        dummy_dict = {
                "loc_id": None, "ref_id": None, "arr_city": None, "dep_city": None,
                "car_distance": None, "car_duration": None, "car_polyline": None,
                "pt_distance": None, "pt_duration": None, "pt_polyline": None, 
                "pt_total_transfers": None
            }

        # loop over all locations and reference locations and look for unprocessed combinations
        for loc in tqdm(locations, "Creating dummies for missing land reachability data..."):
            for start_ref in start_refs:
                if processed_locs[(processed_locs['loc_id'] == loc['location_id']) & (processed_locs['ref_id'] == start_ref['location_id'])].shape[0] == 0:
                    insert_data.append(
                        dummy_dict.update({
                            "loc_id": loc['location_id'],
                            "ref_id": start_ref['location_id'],
                            "arr_city": loc['city'],
                            "dep_city": start_ref['city']
                        })
                    )

    elif mode == "air":

        dummy_dict = {
                "orig_iata": None, "dest_iata": None, "dep_date": None, "total_flights": None, 
                "avg_price": None, "min_price": None, "max_price": None,
                "avg_duration": None, "min_duration": None, "max_duration": None,
                "avg_stops": None
            }
        
        for loc in tqdm(locations, "Creating dummies for missing air reachability data..."):
            for start_ref in start_refs:
                for period in periods:
                    if processed_locs[(processed_locs['orig_iata'] == start_ref['mapped_start_airport']) & (processed_locs['dest_iata'] == loc['airport_1']) & (processed_locs['dep_date'] == period[0])].shape[0] == 0:
                        insert_data.append(
                            dummy_dict.update({
                                "orig_iata": start_ref['mapped_start_airport'],
                                "dest_iata": loc['airport_1'],
                                "dep_date": period[0]
                            })
                        )

    return pd.DataFrame(insert_data)


def process_location_land_reachability(loc: pd.DataFrame, start_refs: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the land reachability of a given location and a set of reference locations.
    Args:
        loc (pd.DataFrame): The location.
        start_refs (pd.DataFrame): The reference locations.
    Returns:
        pd.DataFrame: The land reachability data.
    """

    res = []

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
            tmp_dict['car_distance'] = car_route['distance']
            tmp_dict['car_duration'] = car_route['duration']
            tmp_dict['car_polyline'] = car_route['polyline']
            tmp_dict['car_geojson'] = car_route['geojson']

            # public transport route
            if car_route['duration'] < 3600*20:
                #print("public transport route available")
                pt_route = route.get_public_transport_route(key)
                tmp_dict['pt_distance'] = pt_route['distance']
                tmp_dict['pt_duration'] = pt_route['duration']
                tmp_dict['pt_polyline'] = pt_route['polyline']
                tmp_dict['pt_total_transfers'] = pt_route['total_transfers']
                tmp_dict['pt_geojson'] = pt_route['geojson']

            else:
                print("public transport route not available")
                tmp_dict['pt_distance'] = 0
                tmp_dict['pt_duration'] = 0
                tmp_dict['pt_polyline'] = None
                tmp_dict['pt_total_transfers'] = 0
                tmp_dict['pt_geojson'] = None

        else:
            tmp_dict['car_distance'] = 0
            tmp_dict['car_duration'] = 0
            tmp_dict['car_polyline'] = None
            tmp_dict['pt_distance'] = 0
            tmp_dict['pt_duration'] = 0
            tmp_dict['pt_polyline'] = None
            tmp_dict['pt_total_transfers'] = 0
            tmp_dict['pt_geojson'] = None
        
        # return dataframe of results to be inserted into database
        res.append(pd.DataFrame(tmp_dict, index=[0]))

    db = Database()
    db.connect()
    db.insert_data(pd.concat(res), "raw_reachability_land")
    db.disconnect()
    return None
    

def process_location_air_reachability(loc: pd.DataFrame, start_refs: pd.DataFrame, processed_locs) -> pd.DataFrame:
    """
    Processes the air reachability of a given location airport and a set of reference airports.
    Args:
        loc (pd.DataFrame): The location airport.
        start_refs (pd.DataFrame): The reference airports.
    Returns:
        pd.DataFrame: The air reachability data.
    """

    db = Database()

    # set periods manually: each day of the week one time per season (winter summer); Febrary and March twice (2024 and 2025) because they are closest to the start date
    start_dates = [
        "2024-02-26", "2024-03-05", "2024-04-17", "2024-05-23", "2024-06-28",
        "2024-07-06", "2024-08-11", "2024-09-16", "2024-10-29", "2024-11-06", 
        "2024-12-12", "2025-01-17", 
    ]

    # create destination coordinate dict for Route object constructor
    dest = {
        "lat": float(loc['lat']),
        "lon": float(loc['lon'])
    }

    dest_iata = loc['airport_1'].strip()
    res_list, driver = [], None

    # loop over all periods and reference airports
    for _, row in start_refs.iterrows():
        for dep_date in start_dates:

            orig_iata = row['mapped_start_airport'].strip()

            # manual replacing for destinations in Kazakhstan with airports in Russia (not serviced by Kayak)
            if dest_iata == "ASF":
                dest_iata = "GUW"
            elif dest_iata == "UFA":
                dest_iata = "AKX"

            # all airports in Russia, Iran, and Belarus get no results
            blacklist = ['SVO', 'DME', 'VKO', 'THR', 'LED', 'MHD', 'IKA', 'AER', 'SVX',
                'OVB', 'MSQ', 'SYZ', 'KRR', 'AWZ', 'KIH', 'UFA', 'IFN', 'ROV',
                'KUF', 'KZN', 'KJA', 'MRV', 'VVO', 'KHV', 'IKT', 'TBZ', 'TJM',
                'KGD', 'SGC', 'CEK', 'AAQ', 'PEE', 'BND', 'MCX', 'VOG', 'UUS',
                'GOJ', 'OMS', 'NUX', 'YKS', 'ARH', 'PGU', 'MMK', 'KER', 'AZD',
                'REN', 'NJC', 'PKC', 'ABD', 'TOF', 'BUZ', 'VOZ', 'NBC', 'ASF',
                'ZAH', 'BAX', 'NSK', 'EGO', 'OMH', 'SCW', 'RAS', 'RTW', 'BQS',
                'HTA', 'OGZ', 'STW', 'IJK', 'GDZ', 'SLY', 'MJZ', 'UUD', 'KEJ',
                'CSY', 'ULY', 'NAL', 'HMA', 'CEE', 'IAA', 'GRV', 'IGT', 'NNM',
                'NOJ', 'ABA', 'NOZ', 'NYM', 'KVX', 'USK', 'PEZ', 'MQF', 'BTK',
                'KGP']
            
            # also exclude routes from and to the same airport
            if (dest_iata in blacklist) | (orig_iata == dest_iata):
                db.connect()
                db.insert_data(pd.DataFrame({
                    "orig_iata": orig_iata, "dest_iata": dest_iata,
                    "total_flights": 0, "dep_date": dep_date,
                    "avg_price": None, "min_price": None, "max_price": None,
                    "avg_duration": None, "min_duration": None, "max_duration": None,
                    "avg_stops": None
                }, index=[0]), "raw_reachability_air")
                db.disconnect()
                continue

            # check if flight data for this route and date has already been processed
            if processed_locs[(processed_locs['orig_iata'] == orig_iata) & (processed_locs['dest_iata'] == dest_iata) & (processed_locs['dep_date'] == dep_date)].shape[0] > 0:
                print(f"Already processed flight data for {orig_iata} to {loc['city']} on {dep_date}")
                continue

            else:
                if not driver:
                    driver = webdriver.Chrome(options=configureChromeDriver())

                print(f"Processing {dep_date}, {orig_iata}, {dest_iata}")

                # specify origin coordinates for Route object constructor
                orig = {
                    "lat": float(row['lat']),
                    "lon": float(row['lon'])
                }

                # set origin iata code, create Route object
                route = Route(dest, orig)
                soup = route.getFlightData(driver, orig_iata, dest_iata, dep_date)
                flight_data = route.parseFlightData(orig_iata, dest_iata, dep_date, soup)

                if flight_data == -1:
                    print(f"CAPTCHA detected for {orig_iata} to {loc['city']} on {dep_date}")
                    if driver:
                        driver.quit()
                    driver = webdriver.Chrome(options=configureChromeDriver())
                    continue

                # insert flight data into database
                elif flight_data is not None:
                    flight_data['orig_iata'], flight_data['dest_iata'] = orig_iata, dest_iata
                    res_list.append(pd.DataFrame(flight_data, index=[0]))
                    print(f"SUCCESS: data found for {orig_iata} to {loc['city']} on {dep_date}")
                    db.connect()
                    db.insert_data(pd.DataFrame(flight_data, index=[0]), "raw_reachability_air")
                    db.disconnect()   

                elif flight_data is None:
                    print(f"\033[1;31mWARNING: No flight data found for {orig_iata} to {loc['city']} on {dep_date}\033[0m")

        if driver:
            driver.quit()
                             
    return res_list
