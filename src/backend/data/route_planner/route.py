import requests
from dateutil import parser
import folium
import flexpolyline as fp
import pandas as pd

class Route:
    def __init__(self, origin: tuple, destination: tuple, date: str):
        self.orig = origin
        self.dest = destination
        self.date = date

    def getPublicTransitRoute(self, key, max_distance="2000"):
        """
        Gets the transit route between the origin and destination using the HERE API.
        Args:
            key (str): The HERE API key.
        Returns:
            dict: The route dictionary returned by the HERE API.
        """

        params = {
            "apiKey": key,
            "origin": str(self.orig[0]) + "," + str(self.orig[1]),
            "destination": str(self.dest[0]) + "," + str(self.dest[1]),
            "pedestrian[maxDistance]": max_distance,
            "return": "polyline,intermediate,fares,bookingLinks,travelSummary"
        }

        r = requests.get('https://transit.router.hereapi.com/v8/routes', params=params)

        return r.json()

    
    def getDrivingRoute(self, key):
        """
        Gets the driving route between the origin and destination using the HERE API.

        """

        params = {
            "apiKey": key,
            "origin": str(self.orig[0]) + "," + str(self.orig[1]),
            "destination": str(self.dest[0]) + "," + str(self.dest[1]),
            "transportMode": "car",
            "return": "polyline,summary,travelSummary"
        }

        r = requests.get('https://router.hereapi.com/v8/routes', params=params)

        return r.json()

    def computeTotalTime(self, route):
        """
        Computes the time difference between the departure time at the origin and the arrival time at the destination.
        Args:
            route (dict): The route dictionary returned by the HERE API.
        Returns:
            datetime.timedelta: The time difference between the departure time at the origin and the arrival time at the destination.
        """

        if len(route['routes']) == 0:
            return None

        start = parser.parse(route['routes'][0]['sections'][0]['departure']['time'])
        end = parser.parse(route['routes'][0]['sections'][-1]['arrival']['time'])

        return end - start

    
    def getTotalRouteCoords(self, route):

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

        # Get the coordinates of the route
        coordinates = self.getTotalRouteCoords(route)

        # Create a map centered at the first coordinate
        map_center = coordinates[0]
        mymap = folium.Map(location=map_center, zoom_start=10)

        # Plot the polyline on the map
        folium.PolyLine(locations=coordinates, color="blue").add_to(mymap)

        return mymap
        

    # TODO: Just smallest distance to airport not ideal. Consider top 3-5 airports
    def getNearestAirport(self, airports: str):
        """
        Returns the coordinates and code of the nearest airport to the origin and destination.
        Args:
            airports: The path to the airports.csv file.
        """

        # Calculate the distance between each airport and the origin coordinates
        df = pd.read_csv(airports, sep=";")
        df['distance_orig'] = ((df['Latitude'] - self.orig[0])**2 + (df['Longitude'] - self.orig[1])**2)**0.5
        df['distance_dest'] = ((df['Latitude'] - self.dest[0])**2 + (df['Longitude'] - self.dest[1])**2)**0.5

        # Find the airport code with the smallest distance
        nearest_orig_airp = df.loc[df['distance_orig'].idxmin()]
        nearest_dest_airp = df.loc[df['distance_dest'].idxmin()]

        return {'origin': nearest_orig_airp.to_dict(),
            'destination': nearest_dest_airp.to_dict()}
