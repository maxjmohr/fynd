import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database
import datetime
from geopy.distance import geodesic
import numpy as np
import pandas as pd
import random
import requests
import time

## PARTS ##
# PART 1: Import the csv into the database with Kayak Checks
# PART 2: Find nearest airport for each location
# PART 3: Define start airports and assign to starting locations
############


##====| PART 1: Import the csv into the database with Kayak Checks |====##
class AirportsImporter:
    def __init__(self, db:Database) -> None:
        ''' Initialize the class
        Input:  db: Database object
        Output: None
        '''
        self.db = db


    def import_csv_into_db(self, csv_path:str) -> None:
        ''' Import the csv into the database
        Input:  csv_path: path to the csv
        Output: None
        '''
        # Delete the data in the table
        print(f"{datetime.datetime.now()} - Deleting data in 'core_airports'.")
        self.db.delete_data("core_airports")

        # Read the csv
        print(f"{datetime.datetime.now()} - Reading csv.")
        data = pd.read_csv(csv_path)
        # Get number of columns
        orig_length = len(data.columns)
        assert data is not None, "No data was found in the csv."

        # Deleting the airports that have no latitude or longitude
        print(f"{datetime.datetime.now()} - Deleting airports that have no latitude or longitude.")
        data = data.dropna(subset=["Latitude", "Longitude"])

        # Convert the data in pass_count which is e.g. "103,902,992" to 103902992, so numeric
        print(f"{datetime.datetime.now()} - Converting pass_count to numeric.")
        data["pass_count"] = data["pass_count"].str.replace(",", "").astype(int)

        # Rename columns Latitude and Longitude to lat and lon
        print(f"{datetime.datetime.now()} - Renaming columns.")
        data = data.rename(columns={
            "Latitude": "lat",
            "Longitude": "lon",
            "pass_count": "passenger_count",
            "city_name": "city",
            "country_name": "country"
        })

        # Reorder columns
        print(f"{datetime.datetime.now()} - Reordering columns.")
        data = data[["iata_code", "airport_name", "city", "country", "lat", "lon", "passenger_count"]]
        new_length = len(data.columns)
        assert new_length == orig_length-1, "The length of the data changed during the import process."  # -1 due to deletion of rank

        # Add data to the database
        print(f"{datetime.datetime.now()} - Inserting the data into 'core_airports'.")
        self.db.insert_data(data, "core_airports")


    @staticmethod
    def check_ifexists_kayak(iata_code:str) -> bool:
        ''' Check whether or not an airport can be found on Kayak
        Input:  iata_code: airport code of the airport
        Output: True if the airport can be found on Kayak, False otherwise
        '''
        time.sleep(random.randint(1, 10)/10)
        print(f"{datetime.datetime.now()} - Checking if {iata_code} can be found on Kayak.")
        url = f"https://www.kayak.de/direct/{iata_code}"
        page = requests.get(url)

        if page.status_code == 200:
            print(f"{datetime.datetime.now()} - {iata_code} was found on Kayak.")
            return True
        else:
            print('\033[1m\033[91m{} was not found on Kayak.\033[0m'.format(iata_code))
            return False


    def check_airports(self) -> None:
        ''' Insert airports into the database that were found in Kayak
        Input:  None
        Output: None
        '''
        # Fetch the airports
        print(f"{datetime.datetime.now()} - Fetching airports.")
        airports = self.db.fetch_data(total_object="core_airports")

        # Get the airports that are not yet in the database
        print(f"{datetime.datetime.now()} - Checking if airports can be found in Kayak.")
        airports["exists_on_kayak"] = airports["iata_code"].apply(self.check_ifexists_kayak)
        airports_nokayak = airports[~airports["exists_on_kayak"]]

        # Delete the airports that are not in Kayak
        if len(airports_nokayak) != 0:
            print(f"{datetime.datetime.now()} - Deleting airports that are not in Kayak.")
            for iata_code in airports_nokayak["iata_code"]:
                print(f"{datetime.datetime.now()} - Deleting {iata_code}.")
                sql = f"DELETE FROM core_airports WHERE iata_code = '{iata_code}'"
                self.db.delete_data(sql=sql)
        else:
            print(f"{datetime.datetime.now()} - No airports were found that are not in Kayak.")

"""
db = Database()
db.connect()
AirpImporter = AirportsImporter(db)
current_script_directory = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_script_directory, "../../../../res/master_data/top_airports.csv")
# AirpImporter.import_csv_into_db(path)
AirpImporter.check_airports()
db.disconnect()
"""


##====| PART 2: Find nearest airport for each location |====##
"""
def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    ''' Calculate the great circle distance (km) between two points on the earth (specified in decimal degrees).
    Source: https://stackoverflow.com/a/29546836
    Input:  lon1: longitude of the first point
            lat1: latitude of the first point
            lon2: longitude of the second point
            lat2: latitude of the second point
    Output: km: distance between the two points in km
    '''
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2

    c = 2 * np.arcsin(np.sqrt(a))
    km = 6378.137 * c
    return km
"""


def find_nearest_airports(location:pd.Series, airports:pd.DataFrame) -> pd.DataFrame:
    ''' Find the nearest airport for a given location
    Input:  location: location to find the nearest airport for
            airports: dataframe of all airports
    Output: nearest_airport: nearest airport to the location
    '''
    # Calculate the distance between the location and all airports
    print(f"{datetime.datetime.now()} - Calculating the distance between {location['city']}, {location['country']} and all airports.")
    location = location.copy()
    location["lat"] = pd.to_numeric(location["lat"])
    location["lon"] = pd.to_numeric(location["lon"])

    # For haversine distance
    # airports["distance"] = airports.apply(lambda row: haversine_distance(location["lat"], location["lon"], row["lat"], row["lon"]), axis=1)
    # For geodesic distance
    airports["distance"] = airports.apply(lambda row: geodesic((location["lat"], location["lon"]), (row["lat"], row["lon"])).kilometers, axis=1)

    # Get the top 3 airports
    airports = airports.nsmallest(3, "distance")

    # Calculate sorting metric passenger_count/distance
    # Prefers airports with more passengers and shorter distance
    airports["passenger_count"] = pd.to_numeric(airports["passenger_count"], errors='coerce')
    airports["sorting"] = airports["passenger_count"] / airports["distance"]

    # Get the three nearest airports
    print(f"{datetime.datetime.now()} - Extracting the three nearest airports.")
    nearest_airports = airports.sort_values(by="sorting", ascending=False)

    # Store top 3 airports in a dataframe
    results = pd.DataFrame({
        "location_id": location["location_id"],
        "airport_1": nearest_airports.iloc[0]["iata_code"],
        "airport_2": nearest_airports.iloc[1]["iata_code"],
        "airport_3": nearest_airports.iloc[2]["iata_code"]
    }, index=[0])

    return results


def insert_airport_cols(db:Database, table:str, row:pd.Series) -> None:
    ''' Insert the airports into the database
    Input:  - db: Database
            - table: table to insert the airports into
            - row: row of the results dataframe
    Output: None
    '''
    print(f"{datetime.datetime.now()} - Updating the airports for {row['location_id']} into '{table}'.")
    sql = f"""
        UPDATE {table}
        SET airport_1 = '{row["airport_1"]}', airport_2 = '{row["airport_2"]}', airport_3 = '{row["airport_3"]}'
        WHERE location_id = {row["location_id"]}
    """
    db.execute_sql(sql=sql)


def map_airports_to_loc(db:Database, table:str) -> None:
    ''' Map the airports to the locations
    Input:  - db: Database
            - table: table to map the airports to
    Output: results: dataframe of the results
    '''
    # Fetch the locations and airports
    locations = db.fetch_data(total_object=table)
    airports = db.fetch_data(total_object="core_airports")

    # Find the nearest airports for each location
    print(f"{datetime.datetime.now()} - Finding the nearest airports for each location.")
    results = locations.apply(lambda row: find_nearest_airports(row, airports), axis=1)
    results = pd.concat(results.to_list(), axis=0).reset_index(drop=True)
    print(results)

    # Insert the results into the database
    print(f"{datetime.datetime.now()} - Inserting the airports into '{table}'.")
    results.apply(lambda row: insert_airport_cols(db, table, row), axis=1)
    return results


# Activate to assign nearest airports to locations
"""
db = Database()
db.connect()

# map_airports_to_loc(db, "core_locations")
map_airports_to_loc(db, "core_locations")

db.disconnect()
"""


##====| PART 3: Define start airports and assign to starting locations |====##

def determineUniqueChosenAirport(row, airport_coords):
    closest_airport = min(airport_coords, key=lambda airport: geodesic((row['lat'], row['lon']), (airport_coords[airport]['lat'], airport_coords[airport]['lon'])).meters)
    return closest_airport.iloc[0]["iata_code"]


def map_start_airports_to_start_loc(db:Database, table:str) -> None:
    ''' Map the start airports to the start locations
    Input:  - db: Database
            - table: table to map the start airports to
    Output: None
    '''
    # Fetch the start locations
    start_refs = db.fetch_data(total_object=table)

    # Define start airports
    start_airports = start_refs[start_refs['city'].isin(["Munich", "Frankfurt"])]

    # Create a dictionary with the airport codes and their coordinates
    airport_dict = {code: {'lat': coord['lat'], 'lon': coord['lon']} for code, coord in zip(start_airports['airport_1'], start_airports[['lat', 'lon']].to_dict("records"))}

    # Determine the unique chosen airport for each location
    print(f"{datetime.datetime.now()} - Determining the unique chosen airport for each location.")
    start_refs["mapped_start_airport"] = start_refs.apply(lambda x: determineUniqueChosenAirport(x, airport_dict), axis=1)

    # Insert the results into the database
    print(f"{datetime.datetime.now()} - Inserting the start airports into '{table}'.")
    for _, row in start_refs.iterrows():
        query = f"""
            UPDATE {table}
            SET mapped_start_airport = '{row['mapped_start_airport']}'
            WHERE location_id = {row['location_id']}
        """
        db.execute_sql(query)



# Activate to assign start airports to start location
"""
db = Database()
db.connect()

# Add column to table
#db.execute_sql("ALTER TABLE core_ref_start_locations ADD COLUMN mapped_start_airport VARCHAR(5)")

map_start_airports_to_start_loc(db, "core_ref_start_locations")

db.disconnect()
"""