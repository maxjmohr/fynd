import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
import db_helpers

from Countrydetails import countries
import geojson
from geopy import distance
from geopy.geocoders import Nominatim
import json
from lxml import etree
from math import ceil
import pandas as pd
from random import choice
import requests
from shapely.geometry import Point, mapping
import time
from tqdm import trange
import pandas as pd

update_Wikivoyage_cities = False

###------| Steps |------###
# 1: Get target location names
# 2: Get any relevant geographical data of target locations
# 3: Execute the data gathering and store data in database
###------------###


###------| Step 1: Get target location names |------###

class WikivoyageScraper:
    "Scrape data from Wikivoyage"
    def __init__(self) -> None:
        "Initialize the class: get url and all countries"
        self.url = "https://en.wikivoyage.org/wiki"
        self.countries = countries.all_countries().countries()
        # Change the country names for North Korea and South Korea
        self.countries[self.countries.index("Korea North")] = "North Korea"
        self.countries[self.countries.index("Korea South")] = "South Korea"

    def get_destinations(self, save:bool = True) -> pd.DataFrame:
        ''' Get the destinations from Wikivoyage
        Input:  - self.url
                - self.countries: all countries
                - save: bool, whether to save the dataframe or not
        Output: dataframe with the most relevant destinations per country
        '''
        data_list = []

        for country in self.countries:
            # Print progress and sleep for one second
            time.sleep(1)
            print(f"Getting destinations from {country}...")

            # Get the HTML code
            url_total = f"{self.url}/{country}"
            page = requests.get(url_total).content
            tree = etree.HTML(page)

            # XPath expression to get city and other destination names
            results = list(tree.xpath('//span[@class="fn org listing-name"]/a/text()'))

            # Add location names to dictionary
            data_dict = {}
            if country not in data_dict:
                data_dict[country] = {"city": [], "other_destinations": []}
            if len(results) != 0 and country != "Australia":
                data_dict[country]["city"] = results[:8] # Only the first 9 values are cities
                data_dict[country]["other_destination"] = results[9:] # The rest are other destinations
            elif len(results) != 0 and country == "Australia":
                data_dict[country]["island"] = results[:8] # Only the first 9 values are islands
                data_dict[country]["city"] = results[9:17] # The next 9 values are cities
                data_dict[country]["other_destination"] = results[18:] # The rest are other destinations

            # Store in list
            for country, locations in data_dict.items():
                for location_type, names in locations.items():
                    for name in names:
                        data_list.append({"name": name, "country": country, "type": location_type})
            
        # Store and save dataframe
        data = pd.DataFrame(data_list)
        if save:
            # Combine the current working directory with the relative path
            current_directory = os.getcwd()
            relative_path = "res/master_data/wikivoyage_locations.csv"
            save_path = os.path.join(current_directory, relative_path)
            data.to_csv(save_path, index=False)
            
        return data


def only_cities(data: pd.DataFrame) -> pd.DataFrame:
    ''' Get only the cities from the dataframe
    Input:  df: pd.DataFrame
    Output: pd.DataFrame
    '''
    # Get only the cities
    data = data[data["type"] == "city"].copy()
    # Drop the type column
    data.drop("type", axis=1, inplace=True)
    # Rename column name to city
    data.rename(columns={"name": "city"}, inplace=True)
    # Reset the index
    data.reset_index(drop=True, inplace=True)
    return data


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
        self.county = None
        self.state = None
        self.country = country
        if country is not None:
            self.params = {"city": self.city, "country": self.country}
        else:
            self.params = {"city": self.city}
            print('\033[1m\033[91mWARNING: For city {} no country was specified. This may lead to wrong results.\033[0m'.format(self.city))
        self.shape = shape


    def get_coordinates(self) -> pd.DataFrame:
        ''' Get general information and geographical data on the target location
        Input:  - self.params
                - self.shape
        Output: dataframe with geographical data
        '''
        # API call
        name = ["Felix Koehn", "Max Mohr", "Lukas Schick", "Jakob Zgonc"]
        geolocator = Nominatim(user_agent=choice(name))
        results = geolocator.geocode(query=self.params, exactly_one=True, geometry="geojson", language="en", addressdetails=True, timeout=None)
        
        # Create function to replace German characters
        def replace_german_characters(string: str) -> str:
            ''' Replace German characters in a string
            Input:  original string
            Output: corrected string
            '''
            return string.replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe').replace('ß', 'ss')

        if results is not None:
            results = results.raw

            # Get city, county, state, country and country_code
            self.city = [replace_german_characters(city) for city in results["address"].values()][0] if "address" in results else None
            self.county = replace_german_characters(results["address"]["county"]) if "address" in results and "county" in results["address"] else None
            self.state = replace_german_characters(results["address"]["state"]) if "address" in results and "state" in results["address"] else None
            self.country = replace_german_characters(results["address"]["country"]) if "address" in results and "country" in results["address"] else None
            country_code = results["address"]["country_code"].upper() if "address" in results and "country_code" in results["address"] else None

            # Check if city is assigned
            if self.city is None:
                print('\033[1m\033[91mWARNING: For the city {}, no geographical information could be retrieved.\033[0m'.format(self.city))
                return None

            # Get coordinates and other geographical data
            location_id = results["place_id"]
            address_type = results["addresstype"]
            lat = results["lat"]
            lon = results["lon"]

            # Check if address type is valid (known exception for Prague)
            if address_type not in ["city", "town", "state", "county", "village", "municipality", "island", "region", "province", "leisure", "suburb", "district", "city_district", "state_district", "city_block", "department", "administrative"]:
                print('\033[1m\033[91mWARNING: The address type of {} is {}. This address type is currently not stored.\033[0m'.format(self.city, address_type))
                return None

            # Get bounding box and rearrage it (bottom left (lat&lon) and top right (lat&lon))
            bounding_box = [results["boundingbox"][0], results["boundingbox"][2], results["boundingbox"][1], results["boundingbox"][3]]

            # Calculate radius from from diameter of bounding box divided by 2
            radius_km = ceil(distance.great_circle([bounding_box[0],bounding_box[1]], [bounding_box[2],bounding_box[3]]).km/2)

            # Create dataframe
            data = pd.DataFrame(data = {"location_id": [location_id], "city": [self.city], "county": [self.county], "state": [self.state], "country": [self.country], "country_code": country_code, "address_type": [address_type],
                                        "lat": [lat], "lon": [lon], "radius_km": [radius_km],
                                        "box_bottom_left_lat": [bounding_box[0]], "box_bottom_left_lon": [bounding_box[1]], "box_top_right_lat": [bounding_box[2]], "box_top_right_lon": [bounding_box[3]]})

            # Get geojson
            if "geojson" in results and self.shape == "polygon":
                if results["geojson"]["type"] != "Point":
                    data["geojson"] = json.dumps(results["geojson"])
                else: # Create circle anyway
                    # Create a point
                    point = Point(lon, lat)
                    # Create a circle around the point with a specific radius
                    circle = point.buffer(radius_km / 111.32)
                    # Convert the circle to a GeoJSON object
                    data["geojson"] = json.dumps(geojson.Feature(geometry=mapping(circle))["geometry"])
            elif "geojson" in results and self.shape == "circle":
                # Create a point
                point = Point(lon, lat)
                # Create a circle around the point with a specific radius
                circle = point.buffer(radius_km / 111.32)
                # Convert the circle to a GeoJSON object
                data["geojson"] = json.dumps(geojson.Feature(geometry=mapping(circle))["geometry"])
            elif "geojson" in results and self.shape != "polygon" and self.shape != "circle":
                raise ValueError("Invalid shape. Shape can either be 'polygon' or 'circle'.")
            else:
                data["geojson"] = None
            
        else:
            data = None
    
        return data
    

    def get_population(self) -> pd.DataFrame:
        ''' Get total population and other information of the target location from the OpenDataSoft API
        Input:  - self.city
                - self.country
        Output: dataframe with total population data and other central location information
        '''
        # Try multiple APIs (GeoDB Cities seems to have more accurate data)
        try:
            ###------| First API: GeoDB Cities |------###
            # Here make sure that the city name include the correct special characters
            city = self.city.replace('ue', 'ü').replace('ae', 'ä').replace('oe', 'ö')

            # API call
            base_url = "http://geodb-free-service.wirefreethought.com/v1/geo/places?"
            params = {
                "namePrefix": city,
                "limit": 1,
                "offset": 0,
                "sort": "-population",  # Sort by descending population
                "types": ["CITY", "ISLAND"]
            }
            response = requests.get(base_url, params=params).json()["data"][0]

            # Store variables in a dataframe
            data = pd.DataFrame(data = {"city": [self.city], "population": [response["population"]]})

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
                data = pd.DataFrame(data = {"city": [self.city], "population": [response["population"]]})

            except:
                data = pd.DataFrame(data = {"city": [None], "population": [None]})

        return data
    

    def get_all(self) -> pd.DataFrame:
        ''' Get all data of the target location
        Input:  - self.params
                - shape: str, either "polygon" or "circle"
        Output: dataframe with all data
        '''
        # Get info and coordinates
        data = self.get_coordinates()

        # Get info and population
        if data is not None and data["geojson"] is not None:
            total_population = self.get_population()

            # Merge dataframes and rearrage columns
            data = pd.merge(data, total_population, on="city", how="left")
            data = data[["location_id", "city", "county", "state", "country", "country_code", "address_type", "population", "lat", "lon", "radius_km", "box_bottom_left_lat", "box_bottom_left_lon", "box_top_right_lat", "box_top_right_lon", "geojson"]]
        else:
            data = pd.DataFrame(data = {"location_id": [None], "city": [None], "county": [None], "state": [None], "country": [None], "country_code": [None], "address_type": [None], "population": [None], "lat": [None], "lon": [None], "radius_km": [None], "box_bottom_left_lat": [None], "box_bottom_left_lon": [None], "box_top_right_lat": [None], "box_top_right_lon": [None], "geojson": [None]})
            
        return data


def get_master_data(data: pd.DataFrame, shape: str = "polygon") -> pd.DataFrame:
    ''' Get master data of all cities
    Input:  - cities: pd.DataFrame
            - city: str, name of the city
            - country: str, name of the country
            - shape: str, either "polygon" or "circle"
    Output: dataframe with all master data
    '''
    master_data = pd.DataFrame()

    for i in trange(len(data), desc="Getting master data"):
        # Sleep for one second
        time.sleep(1)
        # Get data
        city = data["city"][i]
        country = data["country"][i]
        print(f"Getting master data for {city}...")
        location_data = LocationMasterData(city=city, country=country, shape=shape).get_all()
        master_data = pd.concat([master_data, location_data], ignore_index=True)
    
    # Delete all duplicates
    master_data.drop_duplicates(inplace=True)
    # Delete all rows where city is None
    master_data.dropna(subset=["city"], inplace=True)
    # Reset the index
    master_data.reset_index(drop=True, inplace=True)

    return master_data

###------| Step 3: Execute the data gathering and store data in database |------###

## Get locations
# Check if data already exists
if os.path.exists("res/master_data/wikivoyage_locations.csv") and update_Wikivoyage_cities == False:
    print("File with locations already exists. Reading file...")
    cities = only_cities(pd.read_csv("res/master_data/wikivoyage_locations.csv"))
else:
    print("File with locations does not exist yet. Creating file...")
    cities = only_cities(WikivoyageScraper().get_destinations(save=True))

## Get master data
master_data = get_master_data(cities, shape="polygon")


## Store data in database
conn, cur, engine = db_helpers.connect_to_db()
db_helpers.create_db_object(conn, cur, object="core_locations")
db_helpers.insert_data(engine, master_data, table="core_locations", if_exists="replace", updated_at=True)
# print(db_helpers.fetch_data(engine, total_object="core_locations"))
db_helpers.disconnect_from_db(conn, cur, engine)