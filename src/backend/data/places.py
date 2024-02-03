import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../"))
sys.path.append(parent_dir)

from database.db_helpers import Database

import datetime
import pandas as pd
import random
import requests
import time


def get_places(location:pd.DataFrame, category:str, shape:str, apikey:str, call_count:int) -> (pd.DataFrame, int):
    ''' Get places of a location and category from the geoapify API
    Input:  - locaation df containing the necessary columns
            - category: category of the places
            - shape: shape of the area. Can either be "box" or "circle"
            - api_key: API key for the geoapify API
            - call_count: number of calls made so far
    Output: places: places of the category in the area
    Weight per call: 1 call per location per caategory for searching 40 places = 2 credits
	Call limits:    - daily: 3,000 credits
    '''
    time.sleep(0.21) # 5 requests per second
    print(f"{datetime.datetime.now()} - Getting places for {location['city']}, category: {category}...")

    # Get places from geoapify API
    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": category,
        "conditions": "named,access", # only named and accessible places
        "limit": 40,
        "apiKey": apikey,
        "format": "json"
    }
    if shape == "box":
        box_bottom_left_lat = location["box_bottom_left_lat"]
        box_bottom_left_lon = location["box_bottom_left_lon"]
        box_top_right_lat = location["box_top_right_lat"]
        box_top_right_lon = location["box_top_right_lon"]
        params["filter"] = f"rect:{box_top_right_lat},{box_bottom_left_lat},{box_top_right_lon},{box_bottom_left_lon}"
    elif shape == "circle":
        lon = location["lon"]
        lat = location["lat"]
        radius = location["radius_km"] * 1000  # convert to m
        params["filter"] = f"circle:{lon},{lat},{radius}"
        params["bias"] = f"proximity:{lon},{lat}"
    else:
        raise ValueError("Invalid shape. Shape can either be 'box' or 'circle'.")
    response = requests.get(url, params=params).json()["features"]

    # Store the relevant columns in lists
    name, lon, lat, categories = [[
        response[i]["properties"][prop] if prop in response[i]["properties"] else None
        for i in range(len(response))
        ]
        for prop in ["name", "lon", "lat", "categories"]
    ]

    # If vegan or vegeterian in categories, add 1
    vegan = [1 if "vegan" in category else 0 for category in categories]
    vegetarian = [1 if "vegetarian" in category else 0 for category in categories]

    # Convert to dataframe
    places = pd.DataFrame({
        "location_id": location["location_id"],
        "place_name": name,
        "place_category": category,
        "lon": lon,
        "lat": lat,
        "vegetarian": vegetarian,
        "vegan": vegan
    })

    if len(places) > 0:
        call_count += 2

    if len(places) == 0:
        print(f"No places found for {location['city']}, category: {category}. Dummy entry created.")
        places = pd.DataFrame({
            "location_id": location["location_id"],
            "place_name": "None found",
            "place_category": category,
            "lon": None,
            "lat": None,
            "vegetarian": None,
            "vegan": None
        }, index=[0])

    # Drop any duplicates in the same category
    places.drop_duplicates(subset=["place_name"], inplace=True)

    return places, call_count

"""
db = Database()
db.connect()

# Get the directory of the current script and store api keys in list
apikeys = []
current_script_directory = os.path.dirname(os.path.abspath(__file__))
path = "../../../res/api_keys/geoapify_apikeys.txt"
with open(os.path.join(current_script_directory, path), "r") as f:
    for line in f:
        apikeys.append(line.strip())
i = 0  # Initialize API key index

# Ensure that exactly 2 API keys are read
'''if len(apikeys) != 2:
    raise ValueError("Expected 2 API keys, but found {}.".format(len(apikeys)))'''

# Read categories
path = "../../../res/master_data/geoapify_rel_categories.csv"
categories = pd.read_csv(os.path.join(current_script_directory, path))
current_state = db.fetch_data(total_object="raw_places")

# For testing: first 2 categories
# categories = categories.iloc[:2]

locations = db.fetch_data(total_object="core_locations")

MAX_RETRIES = 3  # Max number of retries
WAIT_BASE = 1  # Base wait time in seconds
WAIT_MULTIPLIER = 2  # Multiplier for exponential backoff

for category in categories["place_category"]:
    # Create a set of for each location that has not been processed yet for the category
    missing_locations = locations[~locations["location_id"]
                                  .isin(current_state[current_state["place_category"] == category]
                                        ["location_id"])].reset_index(drop=True)
    if len(missing_locations) == 0:
        print(f"All locations have been processed for category {category}.")
        continue

    for location in missing_locations.iterrows():
        # Get places
        for retry in range(MAX_RETRIES):
            try:
                places = get_places(
                    location=location[1],
                    category=category,
                    shape="circle",
                    apikey=apikeys[i]
                )
                db.insert_data(data=places, table="raw_places", updated_at=True)
                break  # Break out of the loop if no exception occurred  

            except Exception as e:
                print(f"An error occurred: {e}")
                print(f"\033[1m\033[91mLimits reached at category {category}. Trying a different API key after some time...\033[0m")
                wait_time = WAIT_BASE * (WAIT_MULTIPLIER ** retry)  # Exponential backoff
                time.sleep(wait_time + random.uniform(-0.5, 0.5))  # Add some randomness
                i = (i + 1) % len(apikeys)  # Switch to the next API key
                continue  # Continue with the next iteration using the next API key

db.disconnect()
"""