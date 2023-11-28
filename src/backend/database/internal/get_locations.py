import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
import db_helpers

import geojson
from geopy import distance
from geopy.geocoders import Nominatim
from math import ceil
import pandas as pd
from random import choice
from shapely.geometry import Point, mapping

###------| Steps |------###
# 1: Get target location names
# 2: Get any relevant geographical data of target locations
# 3: Store data in database
###------------###


###------| Step 1: Get target location names |------###



###------| Step 2: Get any relevant geographical data of target locations |------###

class GeographicalData:
    def __init__(self, city: str, country: str = None) -> None:
        if country is not None:
            self.target = city + ", " + country
        else:
            self.target = city
        name = ["Felix Koehn", "Max Mohr", "Lukas Schick", "Jakob Zgonc"]
        self.geolocator = Nominatim(user_agent=choice(name))

    def get_info_and_coordinates(self, shape: str = "polygon") -> [pd.DataFrame, dict]:
        ''' Get general information and geographical data on the target location
        Input:  - self.target
                - shape: str, either "polygon" or "circle"
        Output: - dataframe with geographical data
                - geojson: geojson of the city
        '''
        # API call
        results = self.geolocator.geocode(query=self.target, exactly_one=True, geometry="geojson", language="en").raw

        # Split the location info using commas and extract columns (information differs from location to location)
        location_info = results["display_name"].replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe').replace('ß', 'ss').split(', ')
        if len(location_info) == 4:
            city = location_info[0]
            district = location_info[1]
            state = location_info[2]
            country = location_info[3]
        elif len(location_info) == 3:
            city = location_info[0]
            district = None
            state = location_info[1]
            country = location_info[2]
        elif len(location_info) == 2:
            city = location_info[0]
            district = None
            state = None
            country = location_info[1]
        elif len(location_info) == 1:
            city = location_info[0]
            district = None
            state = None
            country = None

        # Get coordinates and other geographical data
        location_id = results["place_id"]
        adress_type = results["addresstype"]
        lat = results["lat"]
        lon = results["lon"]

        # Get bounding box and rearrage it (bottom left (lat&lon) and top right (lat&lon))
        bounding_box = [results["boundingbox"][0], results["boundingbox"][2], results["boundingbox"][1], results["boundingbox"][3]]

        # Calculate radius from center to bottom left corner of bounding box in km (always round up)
        radius_km = ceil(distance.great_circle([lat,lon], [bounding_box[0],bounding_box[1]]).km)

        # Create dataframe
        data = pd.DataFrame(data = {"location_id": [location_id], "city": [city], "district": [district], "state": [state], "country": [country], "adress_type": [adress_type],
                                  "lat": [lat], "lon": [lon], "radius_km": [radius_km],
                                  "box_bottom_left_lat": [bounding_box[0]], "box_bottom_left_lon": [bounding_box[1]], "box_top_right_lat": [bounding_box[2]], "box_top_right_lon": [bounding_box[3]]})

        # Get geojson
        if shape == "polygon":
            geo_json = results["geojson"]
        elif shape == "circle":
            # Create a point
            point = Point(lon, lat)
            # Create a circle around the point with a specific radius
            circle = point.buffer(radius_km / 111.32)
            # Convert the circle to a GeoJSON object
            geo_json = geojson.Feature(geometry=mapping(circle))["geometry"]
        else:
            raise ValueError("Invalid shape. Shape can either be 'polygon' or 'circle'.")
    
        return data, geo_json
    
data, geo_json = GeographicalData("Tuebingen", "Germany").get_info_and_coordinates(shape="polygon")

print(data)
#print(geo_json)


###------| Step 3: Store data in database |------###

conn, cur, engine = db_helpers.connect_to_db()
db_helpers.create_db_object(conn, cur, object="core_locations")
db_helpers.insert_data(engine, data, table="core_locations")
print(db_helpers.fetch_data(engine, total_object="core_locations"))
db_helpers.disconnect_from_db(conn, cur, engine)