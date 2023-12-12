import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from data.costs import numbeoScraper
#from data.safety_pipeline import create_country_safety_df
#from data.safety_pipeline import create_city_safety_df
#from data.culture import cultural_profile
from data import geography
from data.weather import SingletonHistWeather, SingletonCurrFutWeather
from database.db_helpers import Database
import numpy as np
import pandas as pd

###----| STEPS |----###
## Step 1: Create and fill tables in database
## Step 2: Fill tables with data
## Step 3: Execute steps 1 and 2 in sequence


####----| STEP 1: CREATE AND FILL TABLES |----####

def create_raw_db_tables(table_names: list, drop_if_exists:bool = False):
    ''' Create tables in the database
    Input:  - table_names: list of names of tables to be created (names of tables must match names of sql-files in objects folder)
            - drop_if_exists: bool, whether to drop the table if it already exists
    Output: None
    '''
    db = Database()
    db.connect()

    for table in table_names:
        db.create_db_object(table, drop_if_exists=drop_if_exists)

    db.disconnect()


def fill_raw_db_tables(table_names):
    ''' Fill tables in the database with data
    Input:  table_names: list of names of tables to be filled
    Output: None
    '''
    # Get list of locations from database
    db = Database()
    db.connect()
    locations_df = db.fetch_data("core_locations")

    # Fill each table
    for table in table_names:
        # Call the fill function
        table_fill_function_dict[table](locations_df, table, db)

    db.disconnect()



####----| STEP 2: FILL TABLES |----####

####----| COSTS |----####
def fill_raw_costs_numbeo(locations: pd.DataFrame, table_name: str, db: Database):
    ''' Get the costs by city or country from numbeo.com
    Input:  - location data
            - table_name: name of the table to insert the data into
            - db: Database objects
    Output: None
    '''
    # Connect to database
    db.delete_data(total_object=table_name, commit=True)

    ns = numbeoScraper()
    ###-- City costs --###
    costs_city = ns.get_costs(by="city")
    
    # Split city column into city and country
    if "(" in costs_city["city"] and ")," not in costs_city["city"]:
        costs_city[["city", "country"]] = costs_city["city"].str.split("(", expand=True)
        costs_city["city"] = costs_city["city"].str.split(",", expand=True)[0]
        costs_city["country"] = costs_city["country"].str.replace(")", "")
    else:
        split_columns = costs_city["city"].str.split(", ", expand=True)
        # Replace None values in column 2 with values from column 1
        split_columns[2] = split_columns[2].combine_first(split_columns[1])
        # Update the costs_city DataFrame with the extracted city and country
        costs_city["city"] = split_columns[0]
        costs_city["country"] = split_columns[2]
    
    # Known issue: Czech Republic (change country value to Czechia)
    costs_city["country"] = costs_city["country"].replace("Czech Republic", "Czechia")

    # Get location_id for each city
    costs_city["location_id"] = costs_city.apply(lambda row: locations[(locations["city"] == row["city"]) & (locations["country"] == row["country"])]["location_id"].values[0] if not locations[(locations["city"] == row["city"]) & (locations["country"] == row["country"])].empty else np.nan, axis=1)

    # Drop all rows where location_id is missing
    costs_city = costs_city.dropna(subset=["location_id"])

    # Reorder columns
    column_order = [
        "location_id", "city", "country",
        "meal_inexp", "meal_mid", "meal_mcdo",
        "bread", "eggs", "cheese", "apples", "oranges", "potato", "lettuce", "tomato", "banana", "onion", "beef", "chicken", "rice",
        "water_small", "water_large", "soda", "milk", "cappuccino", "beer_dom", "beer_imp", "beer_large", "wine",
        "transport_month", "transport_ticket", "taxi_start", "taxi_km", "taxi_hour", "gas",
        "apartment_1room_c", "apartment_1room_o", "apartment_3room_c", "apartment_3room_o", "electricity_water", "internet", "sqm_center", "sqm_suburbs", "mortgage", "phone_plan",
        "gym", "tennis", "cinema",
        "jeans", "dress", "shoes_running", "shoes_business","cigarettes",
        "salary"
        ]
    costs_city = costs_city.reindex(columns=column_order)

    ###-- Country costs --###
    costs_country = ns.get_costs(by="country")
    
    # Add empty location_id and city columns
    costs_country["location_id"] = None
    costs_country["city"] = None

    # Known issue: Czech Republic (change country value to Czechia)
    costs_city["country"] = costs_city["country"].replace("Czech Republic", "Czechia")

    # Reorder columns
    costs_country = costs_country.reindex(columns=column_order)

    ###-- Merge costs --###
    costs = pd.concat([costs_city, costs_country], ignore_index=True)

    ###-- Append to database table --###
    if len(costs) > 0:
        db.insert_data(costs, table_name, if_exists="append")


####----| SAFETY |----####
# creates dataframe ready to be inserted into the raw_safety_city table
def fill_raw_safety_city(location):
    safety_city_df = create_city_safety_df(location["city"])

    return safety_city_df

# creates dataframe ready to be inserted into the raw_safety_country table
def fill_raw_safety_country(location):
    safety_country_df = create_country_safety_df()

    return safety_country_df


####----| CULTURE |----####
# creates dataframe ready to be inserted into the raw_culture table
def fill_raw_culture(location):
    culture_df = cultural_profile(location["lat"]+","+location["lon"])
    culture_df = culture_df.convert_dtypes()

    return culture_df


####----| WEATHER |----####
def fill_raw_weather_current_future(locations: pd.DataFrame, table_name: str, db: Database):
    ''' Get the current and future weather data for a location
    Input: 	- location data
            - table_name: name of the table to insert the data into
            - db: Database objects
    Output: None
    Weight per call: #locations * (#days/14) * (*params/10) -> 1 call = 1 location, 2 weeks, 1 param
	Call limits:    - daily: 10,000 calls
					- hourly: 5,000 calls
					- minute: 600 calls
    '''
    # Delete all data from the table
    db.delete_data(total_object=table_name, commit=True)

    for _, row in locations.iterrows():

        # Get location data
        location_id = row["location_id"]
        city = row["city"]
        country = row["country"]
        lat = row["lat"]
        lon = row["lon"]

        weather_params = {
            # Parameters for all APIs
            "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "sunshine_duration", "daylight_duration", "precipitation_hours",
                    "precipitation_sum", "rain_sum", "snowfall_sum", "wind_speed_10m_max"],
            "timezone": "auto",
            "models": "best_match",
            # Parameters for current and forecast API
            "past_days": 0,
            "forecast_days": 14
            }  # This should account for 1 API call per location
        
        # Initialize API class
        cfw = SingletonCurrFutWeather(params=weather_params, time="current_future")

        # Check if we have reached the call limit (daily)
        if cfw.call_count >= 10001:
            break

        # Get the weather data for the location
        print(f"Getting current and future weather data for {city}")
        weather_df = cfw.get_data(location_id, lat, lon)

        # Append the data to database table
        if len(weather_df) > 0:
            db.insert_data(weather_df, table_name, if_exists="append")


def fill_raw_weather_historical(locations: pd.DataFrame, table_name: str, db: Database):
    ''' Get the historical weather data for a location (aggregated by month and year)
    Input: 	- location data
            - table_name: name of the table to insert the data into
            - db: Database objects
    Output: None
    Weight per call: #locations * (#days/14) * (*params/10) -> 1 call = 1 location, 2 weeks, 1 param
	Call limits:    - daily: 10,000 calls
					- hourly: 5,000 calls
					- minute: 600 calls
    '''
    while True:
    
        # Get the current state from the database
        current_state = db.fetch_data(table_name)

        # For each location get the oldest year and month for which we have data and append it to the dataframe
        current_state = current_state.groupby(["location_id"]).agg({"year": "min", "month": "min"}).reset_index()

        # If locations are missing in current_state, add them with the year 2023 and month 01
        for _, row in locations.iterrows():
            if not row["location_id"] in current_state["location_id"].values:
                current_state = pd.concat([current_state, pd.DataFrame({"location_id": row["location_id"], "year": 2023, "month": 1}, index=[0])], ignore_index=True)
        
        # Order by latest year and month
        current_state = current_state.sort_values(by=["year", "month"], ascending=False)
        # Filter out all locations where we have data until January 2018
        current_state = current_state[(current_state["year"] != 2018) | (current_state["month"] != 1)]

        for _, row in current_state.iterrows():

            # Get location data
            location_id = row["location_id"]
            city = locations[locations["location_id"] == location_id]["city"].values[0]
            country = locations[locations["location_id"] == location_id]["country"].values[0]
            lat = locations[locations["location_id"] == location_id]["lat"].values[0]
            lon = locations[locations["location_id"] == location_id]["lon"].values[0]

            # Get one month of historical data
            # Get the year and month of start and end dates as well as last day of the month
            if row["month"] == 1:
                target_year = row["year"] - 1
                target_month = 12
            else:
                target_year = row["year"]
                target_month = row["month"] - 1
            end_day = 28 if target_month == 2 else 30 if target_month in [4, 6, 9, 11] else 31

            weather_params = {
                # Parameters for all APIs
                "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "sunshine_duration", "daylight_duration", "precipitation_hours",
                        "precipitation_sum", "rain_sum", "snowfall_sum", "wind_speed_10m_max"],
                "timezone": "auto",
                "models": "best_match",
                # Parameters for historical API
                "start_date": f"{target_year}-{str(target_month).zfill(2)}-02",
                "end_date": f"{target_year}-{str(target_month).zfill(2)}-{str(end_day-1)}"
                }  # This should account for 2 API calls per location
            
            # Initialize API class
            hw = SingletonHistWeather(params=weather_params, time="historical")

            # Check if we have reached the call limit (daily)
            if hw.call_count >= 10001:
                break

            # Get the weather data for the location
            print(f"Getting historical weather data for {city}, {country} ({target_year}-{str(target_month).zfill(2)})")
            weather_df = hw.get_data(location_id, lat, lon)

            # Append the data to database table
            if len(weather_df) > 0:
                db.insert_data(weather_df, table_name, if_exists="append")


####----| GEOGRAPHY |----####
# creates dataframe ready to be inserted into the raw_geography table
def fill_raw_geography(location):
    return None



####----| STEP 3: EXECUTE STEPS 1 AND 2 |----####    

# Dictonary that maps names of database tables to functions which fill these tables with data
table_fill_function_dict = {
    #"raw_costs_numbeo": fill_raw_costs_numbeo,
    #"raw_safety_city": fill_raw_safety_city,
    #"raw_safety_country": fill_raw_safety_country,
    #"raw_culture": fill_raw_culture,
    # "raw_weather_current_future": fill_raw_weather_current_future,
    "raw_weather_historical": fill_raw_weather_historical,
    #"raw_geography": fill_raw_geography
    }

# Create tables
# create_raw_db_tables(table_names=table_fill_function_dict.keys(), drop_if_exists=False)
# Fill tables
fill_raw_db_tables(table_names=table_fill_function_dict.keys())