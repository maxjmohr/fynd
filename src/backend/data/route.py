import requests
from dateutil import parser
import folium
import flexpolyline as fp
import pandas as pd
import time
import geocoder
import warnings
import os
from bs4 import BeautifulSoup
from selenium import webdriver


class Route:
    def __init__(self, origin: str, destination: str, date: str):
        self.orig_name = origin
        self.dest_name = destination
        self.orig_coord = self.getCoordinatesByName(origin, "orig")
        self.dest_coord = self.getCoordinatesByName(destination, "dest")
        self.date = date
        self.nearest_airports = self.getNearestAirport()


    def getCoordinatesByName(self, location_name: str, loc_type: str) -> tuple:
        """
        Gets the coordinates of a location by its name using the HERE API.
        Args:
            location_name (str): The name of the location.
            loc_type (str): orig or dest
        Returns:
            tuple: The coordinates of the location.
        """

        global locations_log
    
        # for destinations, check if location is in destination pool, if not, return None. Check if it is in locations_log, if not, add it.
        if loc_type == "dest":
            if location_name in dest_pool:
                if location_name in locations_log['location'].values:
                    return tuple(locations_log[locations_log['location'] == location_name][['lat', 'lon']].values[0])
                
                else:
                    new_location = pd.DataFrame({'location': location_name, 'lat': geocoder.osm(location_name).latlng[0], 'lon': geocoder.osm(location_name).latlng[1]}, index=[0])
                    locations_log = pd.concat([locations_log, new_location], ignore_index=True)
                    locations_log.to_csv("./../../../../res/master_data/locations_log.csv", index=False)

                    return tuple(locations_log[locations_log['location'] == location_name][['lat', 'lon']].values[0])

            else:
                warnings.warn("Destination location not in destination pool. Coordinates cannot be determined.")
                return None

        # for origins, check if location is in locations_log, if not, add it.
        elif loc_type == "orig":
            
            if location_name in locations_log['location'].values:
                    return tuple(locations_log[locations_log['location'] == location_name][['lat', 'lon']].values[0])
                
            else:
                new_location = pd.DataFrame({'location': location_name, 'lat': geocoder.osm(location_name).latlng[0], 'lon': geocoder.osm(location_name).latlng[1]}, index=[0])
                locations_log = pd.concat([locations_log, new_location], ignore_index=True)
                locations_log.to_csv("./../../../../res/master_data/locations_log.csv", index=False)

                return tuple(locations_log[locations_log['location'] == location_name][['lat', 'lon']].values[0])

        else:
            warnings.warn("Invalid location type: Must be either 'orig' or 'dest'.")
            return None
        

    def getPublicTransitRoute(self, key: str, max_distance="2000") -> dict:
        """
        Gets the transit route between the origin and destination using the HERE API.
        Args:
            key (str): The HERE API key.
        Returns:
            dict: The route dictionary returned by the HERE API.
        """

        global num_calls

        if self.orig_coord is None or self.dest_coord is None:
            return None

        params = {
            "apiKey": key,
            "origin": str(self.orig_coord[0]) + "," + str(self.orig_coord[1]),
            "destination": str(self.dest_coord[0]) + "," + str(self.dest_coord[1]),
            "pedestrian[maxDistance]": max_distance,
            "return": "polyline,intermediate,fares,bookingLinks,travelSummary"
        }

        r = requests.get('https://transit.router.hereapi.com/v8/routes', params=params)
        num_calls += 1

        return r.json()

    
    def getDrivingRoute(self, key: str) -> dict:
        """
        Gets the driving route between the origin and destination using the HERE API.

        """

        if self.orig_coord is None or self.dest_coord is None:
            return None

        global num_calls

        params = {
            "apiKey": key,
            "origin": str(self.orig_coord[0]) + "," + str(self.orig_coord[1]),
            "destination": str(self.dest_coord[0]) + "," + str(self.dest_coord[1]),
            "transportMode": "car",
            "return": "polyline,summary,travelSummary"
        }

        r = requests.get('https://router.hereapi.com/v8/routes', params=params)
        num_calls += 1

        return r.json()
    

    def getAirlineRoute(self) -> dict:
        """
        Gets the airline route between the origin and destination using the custom KAYAK scraper.
        """

        cheapest, best = {}, {}

        flights = getFlightDetails(self.nearest_airports['origin']['code'], self.nearest_airports['destination']['code'], self.date)

        for i, full_desc in enumerate(flights['full_desc']):
            if "Best" in full_desc:
                best['full_desc'] = flights['full_desc'][i]
                best['price'] = flights['price'][i]
                best['duration'] = flights['duration'][i]
                best['time'] = flights['time'][i]
                best['stops'] = flights['stops'][i]
                break

        for i, full_desc in enumerate(flights['full_desc']):
            if "Cheapest" in full_desc:
                best['full_desc'] = flights['full_desc'][i]
                best['price'] = flights['price'][i]
                best['duration'] = flights['duration'][i]
                best['time'] = flights['time'][i]
                best['stops'] = flights['stops'][i]
                break

        if cheapest is None and best is None:
            warnings.warn("No flights found for this route.")
            return None
        
        else:
            return {'cheapest': cheapest, 'best': best}
            

    def computeTotalTime(self, route) -> float:
        """
        Computes the time difference between the departure time at the origin and the arrival time at the destination.
        Args:
            route (dict): The route dictionary returned by the HERE API.
        Returns:
            datetime.timedelta: The time difference between the departure time at the origin and the arrival time at the destination.
        """

        assert route is not None

        if len(route['routes']) == 0:
            return None

        start = parser.parse(route['routes'][0]['sections'][0]['departure']['time'])
        end = parser.parse(route['routes'][0]['sections'][-1]['arrival']['time'])

        return end - start

    
    def getTotalRouteCoords(self, route) -> list:

        assert route is not None

        if len(route['routes']) == 0:
            return None

        coords = []

        for section in route['routes'][0]['sections']:
            coords.extend(fp.decode(section['polyline']))

        return coords

    
    def plotRoute(self, route):
        """
        Plots a route on a map using folium.
        Args:
            coordinates (list): List of coordinate tuples.
        Returns:
            folium.Map: The map with the route plotted on it.
        """

        assert route is not None

        # Get the coordinates of the route
        coordinates = self.getTotalRouteCoords(route)

        # Create a map centered at the first coordinate
        map_center = coordinates[0]
        mymap = folium.Map(location=map_center, zoom_start=10)

        # Plot the polyline on the map
        folium.PolyLine(locations=coordinates, color="blue").add_to(mymap)

        return mymap
        

    # TODO: Just smallest distance to airport not ideal. Consider top 3-5 airports
    def getNearestAirport(self) -> dict:
        """
        Returns the coordinates and code of the nearest airport to the origin and destination.
        Args:
            airports: The path to the airports.csv file.
        """

        # Calculate the distance between each airport and the origin coordinates
        df = pd.read_csv("./../../../../res/master_data/airports.csv")        
        df['distance_orig'] = ((df['Latitude'] - self.orig[0])**2 + (df['Longitude'] - self.orig[1])**2)**0.5
        df['distance_dest'] = ((df['Latitude'] - self.dest[0])**2 + (df['Longitude'] - self.dest[1])**2)**0.5

        # Find the airport code with the smallest distance
        nearest_orig_airp = df.loc[df['distance_orig'].idxmin()]
        nearest_dest_airp = df.loc[df['distance_dest'].idxmin()]

        return {'origin': nearest_orig_airp.to_dict(),
            'destination': nearest_dest_airp.to_dict()}
    

# TODO: incorporate flight fetcher
# TODO: complete route selection algorithm (based on distance, time, price, etc.)


def setUserRoute(origin: str, dest: str, date: str) -> Route:
    """
    Sets the user route. origin, destination and date will be user inputs. 
    Args:
        origin (str): name of origin
        dest (str): name of destination
        date (str): The date of departure.
    """

    return Route(origin, dest, date)


# UTILITY functions ------------------------------------------------------------------------ # 
def getFlightDetails(orig: str, dest: str, date_leave: str) -> dict:
    """
    Returns a dictionary containing the flight details for a given query.
    Input: orig (string): origin airport code
        dest (string): destination airport code
        date_leave (string): departure date in format YYYY-mm-dd
    """

    # TODO: is there a way to make it faster with selenium?
    url = f"https://www.kayak.com/flights/{orig}-{dest}/{date_leave}?sort=bestflight_a"
    driver = webdriver.Chrome()
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    res = {
        'origin': orig,
        'destination': dest,
        'date_leave': date_leave,
        'duration': [],
        'stops': [],
        'time': [],
        'price': [],
        'full_desc': [],
        'best': [],
        'cheapest': []
    }

    # Loop through each nrc6-inner element
    for nrc6_element in soup.select('.nrc6-inner'):
        vmXl_elements = nrc6_element.select('.vmXl-mod-variant-default')
        res['stops'].append(vmXl_elements[0].text)
        res['duration'].append(vmXl_elements[1].text)
        res['time'].append(nrc6_element.select('.vmXl-mod-variant-large')[0].text)
        res['price'].append(int(nrc6_element.select('.f8F1-price-text')[0].text[1:].replace(',', '')))
        res['full_desc'].append(nrc6_element.text)

    res['cheapest'] = [True if "Cheapest" in x else False for x in res['full_desc']]
    res['best'] = [True if "Best" in x else False for x in res['full_desc']]

    return res

def getAPIcalls():
    """
    Logs the number of API calls made today.
    """

    with open("here_api.log", "r") as f:

        lines = f.readlines()
        for line in lines:
            if time.strftime("%Y-%m-%d") in line.split():
                return int(line.split()[1])

        return 0


def logAPIcalls():
    """
    Logs the number of API calls made today.
    """
    with open("here_api.log", "a") as f:
        f.write(time.strftime("%Y-%m-%d") + " " + str(num_calls) + "\n")

        return None


def main():

    # LOAD RESOURCES ---------------------------------------------------------------------------- #

    # read routes.log file to check number of available API calls today (limit: 1000 per day)
    global num_calls
    num_calls = getAPIcalls()
    print(num_calls, type(num_calls))

    # read key from text file
    with open("./../../../../res/auth/here_key.txt", "r") as f:
        key = f.read()

    # set destination pool: destinations in wikivoyage_destinations.csv that are of type 'city'
    # TODO: expand to other types of destinations
    wv_destinations = pd.read_csv("./../../../../res/master_data/wikivoyage_locations.csv")
    global dest_pool
    dest_pool = wv_destinations[wv_destinations['type'] == 'city']["name"].values

    # load locations log file
    global locations_log
    if os.path.exists("./../../../../../res/master_data/locations_log.csv"):
        locations_log = pd.read_csv("./../../../../../res/master_data/locations_log.csv")
    else:
        locations_log = pd.DataFrame(columns=['location', 'lat', 'lon'])


    # PERFOM ROUTE CALCULATION ---------------------------------------------------------------------------- #

    # set some sample origins and destinations
    origin = "Hamburg"
    destination = ["Reykjavík"]
    date = "2024-01-10"

    # create route objects, create public transit, driving routes and air route
    routes = [Route(origin, dest, date) for dest in destination]
    public_transit_routes = [route.getPublicTransitRoute(key) for route in routes]
    driving_routes = [route.getDrivingRoute(key) for route in routes]

    # get driving and transit route maps
    public_transit_maps = [route.plotRoute(transit_directions) for route, transit_directions in zip(routes, public_transit_routes)]
    driving_maps = [route.plotRoute(transit_directions) for route, transit_directions in zip(routes, public_transit_routes)]


    public_transit_maps[4].show_in_browser()


    # LOG API CALLS ---------------------------------------------------------------------------- #
    logAPIcalls()


if __name__ == "__main__":
    main()