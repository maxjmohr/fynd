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
import requests
from shapely.geometry import Point, mapping
import pandas as pd

###------| Steps |------###
# 1: Get target location names
# 2: Get any relevant geographical data of target locations
# 3: Store data in database
###------------###


###------| Step 1: Get target location names |------###

"""# Read test citiess
data = pd.read_csv("test_cities.csv")

# Print the DataFrame
print(data)"""


###------| Step 2: Get any master data of target locations |------###

class LocationMasterData:
    def __init__(self, city: str, country: str = None, shape: str = "polygon") -> None:
        ''' Initialize the class
        Input:  - city: str, name of the city
                - country: str, name of the country
                - shape: str, either "polygon" or "circle"
        Output: None
        '''
        self.city = city
        self.district = None
        self.state = None
        self.country = country
        if country is not None:
            self.target = city + ", " + country
        else:
            self.target = city
            print('\033[1m\033[91mWARNING: For city {} no country was specified. This may lead to wrong results.\033[0m'.format(self.city))
        self.shape = shape


    def get_coordinates(self) -> [pd.DataFrame, dict]:
        ''' Get general information and geographical data on the target location
        Input:  - self.target
                - self.shape
        Output: - dataframe with geographical data
                - geojson: geojson of the city
        '''
        # API call
        name = ["Felix Koehn", "Max Mohr", "Lukas Schick", "Jakob Zgonc"]
        geolocator = Nominatim(user_agent=choice(name))
        results = geolocator.geocode(query=self.target, exactly_one=True, geometry="geojson", language="en").raw

        # Split the location info using commas and extract columns (information differs from location to location)
        location_info = results["display_name"].replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe').replace('ß', 'ss').split(', ')
        if len(location_info) == 6:
            self.city = location_info[0]
            self.district = location_info[2]
            self.state = location_info[3]
            self.country = location_info[5]
        elif len(location_info) == 5:
            self.city = location_info[0]
            self.district = location_info[1]
            self.state = location_info[2]
            self.country = location_info[4]
        if len(location_info) == 4:
            self.city = location_info[0]
            self.district = location_info[1]
            self.state = location_info[2]
            self.country = location_info[3]
        elif len(location_info) == 3:
            self.city = location_info[0]
            self.state = location_info[1]
            self.country = location_info[2]
        elif len(location_info) == 2:
            self.city = location_info[0]
            self.country = location_info[1]
        elif len(location_info) == 1:
            self.city = location_info[0]

        # Check if city is assigned
        if self.city is None:
            raise ValueError("City geographical information could not be retrieved.")

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
        data = pd.DataFrame(data = {"location_id": [location_id], "city": [self.city], "district": [self.district], "state": [self.state], "country": [self.country], "adress_type": [adress_type],
                                    "lat": [lat], "lon": [lon], "radius_km": [radius_km],
                                    "box_bottom_left_lat": [bounding_box[0]], "box_bottom_left_lon": [bounding_box[1]], "box_top_right_lat": [bounding_box[2]], "box_top_right_lon": [bounding_box[3]]})

        # Get geojson
        if self.shape == "polygon":
            geo_json = results["geojson"]
        elif self.shape == "circle":
            # Create a point
            point = Point(lon, lat)
            # Create a circle around the point with a specific radius
            circle = point.buffer(radius_km / 111.32)
            # Convert the circle to a GeoJSON object
            geo_json = geojson.Feature(geometry=mapping(circle))["geometry"]
        else:
            raise ValueError("Invalid shape. Shape can either be 'polygon' or 'circle'.")
    
        return data, geo_json
    

    def get_population(self) -> pd.DataFrame:
        ''' Get total population and other information of the target location from the OpenDataSoft API
        Input:  - self.city
                - self.countrys
        Output: dataframe with total population data and other central location information
        '''
        # Try multiple APIs (GeoDB Cities seems to have more accurate data)
        try:
            ###------| First API: GeoDB Cities |------###
            # Here make sure that the city name include the correct special characters
            city = self.city.replace('ue', 'ü').replace('ae', 'ä').replace('oe', 'ö').replace('s', 'ß')

            # API call
            base_url = "http://geodb-free-service.wirefreethought.com/v1/geo/places?"
            params = {
                "namePrefix": city,
                "limit": 1,
                "offset": 0,
                "sort": "-population"
            }
            response = requests.get(base_url, params=params).json()["data"][0]

            # Store variables in a dataframe
            data = pd.DataFrame(data = {"city": [self.city], "country_code": [response["countryCode"]], "population": [response["population"]]})

        except:
            try:
                ###------| Second API: OpenDataSoft |------###
                # API call
                url_basis = "https://documentation-resources.opendatasoft.com/api/explore/v2.1/catalog/datasets/geonames-all-cities-with-a-population-1000/records"
                select = "select=name%2C%20alternate_names%2C%20country_code%2C%20cou_name_en%2C%20population%2C%20timezone%2C%20modification_date"
                if self.country is not None:
                    where = f"where=alternate_names%3D%22{self.city}%22%20and%20cou_name_en%3D%22{self.country}%22"
                else:
                    where = f"where=alternate_names%3D%22{self.city}%22"
                url = f"{url_basis}?{select}&{where}&limit=1"
                response = requests.get(url).json()["results"][0]

                # Store variables in a dataframe
                data = pd.DataFrame(data = {"city": [self.city], "country_code": [response["country_code"]], "population": [response["population"]]})

            except:
                data = pd.DataFrame(data = {"city": [None], "country_code": [None], "population": [None]})

        return data
    

    def get_all(self) -> [pd.DataFrame, dict]:
        ''' Get all data of the target location
        Input:  - self.target
                - shape: str, either "polygon" or "circle"
        Output: - dataframe with all data
                - geojson: geojson of the city
        '''
        # Get info and coordinates
        data, geo_json = self.get_coordinates()

        # Get info and population
        total_population = self.get_population()

        # Merge dataframes and rearrage columns
        data = pd.merge(data, total_population, on="city", how="left")
        data = data[["location_id", "city", "district", "state", "country", "country_code", "adress_type", "population", "lat", "lon", "radius_km", "box_bottom_left_lat", "box_bottom_left_lon", "box_top_right_lat", "box_top_right_lon"]]

        return data, geo_json
    
data, geo_json = LocationMasterData(city="Buxtehude", country="Germany", shape="polygon").get_all()

print(data)
#print(geo_json)


###------| Step 3: Store data in database |------###

"""conn, cur, engine = db_helpers.connect_to_db()
db_helpers.create_db_object(conn, cur, object="core_locations")
db_helpers.insert_data(engine, data, table="core_locations", if_exists="replace")
print(db_helpers.fetch_data(engine, total_object="core_locations"))
db_helpers.disconnect_from_db(conn, cur, engine)"""