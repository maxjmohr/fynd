import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from data.costs import numbeoScraper
from data.health import get_health_info, get_legatum_health_score
from  data.places import get_places
from data.safety import create_country_safety_df
from data.safety import create_city_safety_df
from data.weather import SingletonHistWeather, SingletonCurrFutWeather
from data.accomodations import generate_periods, process_period
from data.reachability import (process_location_land_reachability, 
                               process_location_air_reachability, 
                               fill_reachibility_table)
from database.db_helpers import Database
import datetime
from dateutil.relativedelta import relativedelta
import ee
from geopy.distance import geodesic
import json
from multiprocessing import Pool
import numpy as np
import pandas as pd
import random
import time
from tqdm import tqdm

###----| STEPS |----###
## Step 1: Functions to create and fill tables in database
## Step 2: Functions to create logging
## Step 3: Fill tables with data
## Step 4: Execute steps 1, 2 and 3


####----| STEP 1: FUNCTIONS TO CREATE AND FILL TABLES |----####

def create_raw_db_tables(db: Database, table_names: list, drop_if_exists:bool = False):
    ''' Create tables in the database
    Input:  - database
            - table_names: list of names of tables to be created (names of tables must match names of sql-files in objects folder)
            - drop_if_exists: bool, whether to drop the table if it already exists
    Output: None
    '''
    for table in table_names:
        db.create_db_object(table, drop_if_exists=drop_if_exists)


def fill_raw_db_tables(db: Database, table_names):
    ''' Fill tables in the database with data
    Input:  - database
            - table_names: list of names of tables to be filled
    Output: None
    '''
    # Get list of locations from database
    locations_df = db.fetch_data("core_locations")
    
    # Fill each table
    for table in table_names:
        start_datetime = datetime.datetime.now()
        try:
            #call fill-function, insert into table
            end_datetime = table_fill_function_dict[table][0](locations = locations_df, table_name = table, db = db)
            exit_code = 0
            
        except Exception as error:
            print("Error when inserting into " + table + ":", type(error).__name__, "–", error)
            end_datetime = datetime.datetime.now()
            exit_code = 1
            
        finally:
            fill_log_history_db_table(process_id=table_fill_function_dict[table][1],
                                      start_datetime=start_datetime,
                                      status="Done",
                                      end_datetime=end_datetime,
                                      exit_code=exit_code)



####----| STEP 2: FUNCTIONS TO CREATE LOGGING |----####

# takes a list of table names and sets up these tables in the database
# names of tables must match names of sql-files in objects folder
def create_log_db_tables(db : Database, table_names):

    for table in table_names:
        db.create_db_object(table)
        
        
# fills log_processes table in database with information on data insertion processes, takes process ids as input
def fill_log_processes_db_table(db : Database, process_ids):

    # get data from log_history table
    log_history = db.fetch_data("log_history")

    # initialize empty dataframe which stores process information
    log_processes_df = pd.DataFrame({'process_id' : [],
                                     'description' : [],
                                     'script_params' : [],
                                     'turnus' : [],
                                     'last_exec' : [],
                                     'next_exec_scheduled' : []})

    # for each process 
    for process in process_ids:
        # try to get time of last insertion process, next insertion process according to turnus
        try:
            process_history = log_history[log_history["process_id"] == process] \
            .sort_values(by="last_exec", ascending=False).reset_index()

            last_exec = process_history.loc[0, "last_exec"]

            next_exec_scheduled = process_history.loc[0, "next_exec_scheduled"]

        # if history for this process is not available, set last execution to standard Unix time 
        # and time of next scheduled insertion process to now
        except:
            last_exec = datetime.datetime(1970, 1, 1)
            next_exec_scheduled = datetime.datetime.now()

        # create dataframe row with information for the process
        new_row = pd.DataFrame({'process_id' : [process],
                                'description' : [table_process_id_dict[process][1]],
                                'script_params' : [table_process_id_dict[process][0]],
                                'turnus' : [table_process_id_dict[process][2]],
                                'last_exec' : [last_exec],
                                'next_exec_scheduled' : [next_exec_scheduled]})
        
        # add to dataframe
        log_processes_df = pd.concat([log_processes_df, new_row], ignore_index=True)
    
    # insert complete dataframe into database table
    db.insert_data(log_processes_df, "log_processes", updated_at=False)


# fills log_history table in database with information on latest insertion operations into database tables
def fill_log_history_db_table(process_id, start_datetime, status, end_datetime, exit_code):

    # get data from log_history and log_processes tables
    log_history = db.fetch_data("log_history")
    log_processes_df = db.fetch_data("log_processes")


    # try to get time of last insertion process, next insertion process according to turnus
    try:
        process_history = log_history[log_history["process_id"] == process_id] \
        .sort_values(by="last_exec", ascending=False).reset_index()

        last_exec = process_history.loc[0, "last_exec"]

        next_exec_scheduled = process_history.loc[0, "next_exec_scheduled"]

    # if history for this process is not available, set last execution to now
    # and time of next scheduled insertion process to now + turnus
    except:
        last_exec = datetime.datetime.now()
        next_exec_scheduled = last_exec + relativedelta(days=table_process_id_dict[process_id][2])


    # initialize empty dataframe which stores process log information
    log_history_df = pd.DataFrame({'process_id' : [process_id],
                                    'start_datetime' : [start_datetime],
                                    'status' : [status],
                                    'end_datetime' : [end_datetime],
                                    'exit_code' : [exit_code],
                                    'triggered' : ["manually"],
                                    'last_exec' : [last_exec],
                                    'next_exec_scheduled' : [next_exec_scheduled]})
    
    # update log_processes with new last_exec and next_exec_scheduled times
    log_processes_df.loc[log_processes_df["process_id"]==process_id, "last_exec"] = last_exec
    log_processes_df.loc[log_processes_df["process_id"]==process_id, "next_exec_scheduled"] = next_exec_scheduled
    
    # insert data into log_history and log_processes tables
    db.insert_data(log_history_df, "log_history", updated_at=False)
    db.insert_data(log_processes_df, "log_processes", updated_at=False, if_exists='replace')



####----| STEP 3: FILL TABLES |----####

####----| COSTS |----####
def fill_raw_accommodation_costs(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:
    """
    Fill function for raw accommodation costs table
    Args:
        locations: DataFrame with locations
        table_name: name of the table in the database
        db: Database object

    Returns:
        datetime.datetime: end datetime
    """

    num_workers = 2
    today_2025 = str(datetime.datetime.now().date()).replace("2024", "2025")
    periods = generate_periods("2024-02-17", today_2025, 14)

    # check which periods still need to be processed by checking the database
    db = Database()
    db.connect()
    raw_acc = db.fetch_data("raw_accommodation_costs")
    db.disconnect()

    # remove fully processed periods, sort by start_date to get earlier start date first
    rem_periods = [period for period in periods if raw_acc[raw_acc['start_date'] == period[0].date()].shape[0] < 722]
    rem_periods = sorted(rem_periods, key=lambda x: x[0])

    with Pool(num_workers) as p:
        p.map(process_period, rem_periods)

    end_datetime = datetime.datetime.now()

    return end_datetime


def fill_raw_costs_numbeo(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:
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

    # Reorder columns
    costs_country = costs_country.reindex(columns=column_order)

    ###-- Merge costs and slight adaption--###
    costs = pd.concat([costs_city, costs_country], ignore_index=True)

    # Known issues: Change some country names
    costs["country"] = costs["country"].replace("Czech Republic", "Czechia")
    costs["country"] = costs["country"].replace("Bosnia And Herzegovina", "Bosnia and Herzegovina")

    # Known issue: Hong Kong (change country and city values where country = "Hong Kong (China)")
    costs.loc[costs["country"] == "Hong Kong (China)", "country"] = "China"
    costs.loc[costs["country"] == "Hong Kong (China)", "city"] = "Hong Kong"


    ###-- Append to database table --###
    if len(costs) > 0:
        db.insert_data(costs, table_name, if_exists="append")

    # Get current time for logging and return it
    end_datetime = datetime.datetime.now()

    return end_datetime



####----| SAFETY |----####
def fill_raw_safety_city(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:
    ''' Get the safety information for a city
    Input: 	- location data
            - table_name: name of the table to insert the data into
            - db: Database objects
    Output: None
    '''
    # For each location call create_city_safety_df to get safety information for this location
    for _, row in locations.iterrows():
        safety_city_df = create_city_safety_df(row["city"])

        # If information could be found for this location, insert it into the database
        if len(safety_city_df) > 0:
            db.insert_data(safety_city_df, table_name, if_exists="append")

    # Get current time for logging and return it
    end_datetime = datetime.datetime.now()

    return end_datetime

def fill_raw_safety_country(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:
    ''' Get the safety information for a country
    Input: 	- location data
            - table_name: name of the table to insert the data into
            - db: Database objects
    Output: None
    '''
    # Get safety information for all countries
    safety_country_df = create_country_safety_df()

    # If information could be found, insert it into the database
    if len(safety_country_df) > 0:
        db.insert_data(safety_country_df, table_name, if_exists="append")

    # Get current time for logging and return it
    end_datetime = datetime.datetime.now()

    return end_datetime

  
  
####----| REACHABILITY |----####
def fill_raw_reachability_land(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:

    # create the unique chosen airport column (binary for each reference start location by closer distance to FRA or MUC)
    db.connect()
    start_refs = db.fetch_data("core_ref_start_locations")
    processed_locs = db.fetch_data("raw_reachability_land")

    # create default values using imported function from reachability module, insert that into "table_name"
    insert_data = fill_reachibility_table(locations, start_refs, processed_locs, table_name, db)
    db.insert_data(insert_data, table_name, if_exists='append')
    db.disconnect()

    # remove locations for which data was already scraped (one row for each reference start location)
    rem_loc_ids = [loc for loc in locations['location_id'].values if processed_locs[processed_locs['loc_id'] == loc].shape[0] < start_refs.shape[0]]
    locations = locations[locations['location_id'].isin(rem_loc_ids)]

    # iterate over locations
    for _, loc in locations.iterrows():

        # module function returns a dataframe with combinations for all start locations and the current location
        loc_land_reachability_df = process_location_land_reachability(loc, start_refs)

        # insert that into "table_name" if it is not empty
        if len(loc_land_reachability_df) > 0:
            db.insert_data(loc_land_reachability_df, table_name, if_exists='append')

    end_datetime = datetime.datetime.now()

    return end_datetime 


def process_location_land_reachability_wrapper(args):
    return process_location_land_reachability(*args)

def fill_raw_reachability_land_par(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:
    # create the unique chosen airport column (binary for each reference start location by closer distance to FRA or MUC)
    db.connect()
    start_refs = db.fetch_data("core_ref_start_locations")
    processed_locs = db.fetch_data("raw_reachability_land")

    # create default values using imported function from reachability module, insert that into "table_name"
    #insert_data = fill_reachibility_table(locations, start_refs, processed_locs, table_name, db)
    #db.insert_data(insert_data, table_name, if_exists='append')
    #db.disconnect()

    # remove locations for which data was already scraped (one row for each reference start location)
    rem_loc_ids = [loc for loc in locations['location_id'].values if processed_locs[processed_locs['loc_id'] == loc].shape[0] < start_refs.shape[0]]
    locations = locations[locations['location_id'].isin(rem_loc_ids)]

    num_workers = 5

    # create a pool of processes
    with Pool(num_workers) as pool:
        # prepare the arguments for process_location_land_reachability()
        args = [(loc, start_refs) for _, loc in locations.iterrows()]
        # use pool.map() to run process_location_land_reachability() in parallel for all locations
        results = pool.map(process_location_land_reachability_wrapper, args)

        
def fill_raw_reachability_air(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:
    """
    Fill function for raw reachability air table
    Args:
        locations: DataFrame with locations
        table_name: name of the table in the database
        db: Database object

    Returns:
        datetime.datetime: end datetime
    """

    # create the unique chosen airport column (binary for each reference start location by closer distance to FRA or MUC)
    db.connect()
    start_refs = db.fetch_data("core_ref_start_locations")
    db.disconnect()
    
    # use only start reference locations with unique chosen iata
    start_refs = start_refs.drop_duplicates(subset=['mapped_start_airport'])

    # drop duplicates of first airport to create unique orig -> dest combinations
    locations = locations.drop_duplicates(subset=['airport_1'])

    # remove locations for which data was already scraped
    try:
        db.connect()
        raw_reachability = db.fetch_data("raw_reachability_air")
        db.disconnect()

    except:
        raw_reachability = None

    # iterate over locations
    for _, loc in locations.iterrows():

        # module function returns a dataframe with combinations for all start locations and the current location
        loc_air_reachability_df = process_location_air_reachability(loc, start_refs, raw_reachability)

        # insert that into "table_name" if it is not empty
        if len(loc_air_reachability_df) > 0:
            db.insert_data(loc_air_reachability_df, table_name, if_exists='append')

    end_datetime = datetime.datetime.now()

    return end_datetime


def worker(args: list):
    """
    Worker function for multiprocessing execution of fill_raw_reachability_air_par function
    """
    loc, start_refs, raw_reachability = args
    return process_location_air_reachability(loc, start_refs, raw_reachability)


def fill_raw_reachability_air_par(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:
    """
    Fill function for raw reachability air table in parallel
    Args:
        locations: DataFrame with locations
        table_name: name of the table in the database
        db: Database object

    Returns:
        datetime.datetime: end datetime
    """

    num_workers = 5

    # create the unique chosen airport column (binary for each reference start location by closer distance to FRA or MUC)
    db.connect()
    start_refs = db.fetch_data("core_ref_start_locations")
    raw_reachability = db.fetch_data("raw_reachability_air")
    db.disconnect()
    
    # use only start reference locations with unique chosen iata
    start_refs = start_refs.drop_duplicates(subset=['mapped_start_airport'])

    # drop duplicates of first airport to create unique orig -> dest combinations
    locations = locations.drop_duplicates(subset=['airport_1'])
    locations = locations[~locations['country'].isin(["Belarus", "Russia", "Iran"])] # Kayak shows no results for some countries due to poltical reasons

    start_dates = [
        "2024-02-26", "2024-03-05", "2024-04-17", "2024-05-23", "2024-06-28",
        "2024-07-06", "2024-08-11", "2024-09-16", "2024-10-29", "2024-11-06", 
        "2024-12-12", "2025-01-17", 
    ]

    # use only start reference locations with unique chosen iata
    start_refs = start_refs.drop_duplicates(subset=['mapped_start_airport'])

    # drop duplicates of first airport to create unique orig -> dest combinations
    locations = locations.drop_duplicates(subset=['airport_1'])
    locations = locations[~locations['country'].isin(["Belarus", "Russia", "Iran"])] # Kayak shows no results for some countries due to poltical reasons

    # keep only locations that have not been fully processed yet
    not_fully_processed = []
    for ap in locations['airport_1'].values.tolist():
        for start_ref in start_refs['mapped_start_airport'].values.tolist():
            if raw_reachability[(raw_reachability['dest_iata'] == ap) & (raw_reachability['orig_iata'] == start_ref)].shape[0] < len(start_dates):
                not_fully_processed.append(ap)
                break

    locations = locations[locations['airport_1'].isin(pd.Series(not_fully_processed))]
    locations['missing'] = locations['airport_1'].apply(lambda x: x not in raw_reachability['dest_iata'].unique())
    locations = locations.sort_values(by=['missing', 'country'], ascending=False)

    # create a multiprocessing Pool with the specified number of workers
    with Pool(num_workers) as p:
        results = p.map(worker, [(loc, start_refs, raw_reachability) for _, loc in locations.iterrows()])

    end_datetime = datetime.datetime.now()

    return end_datetime
  


####----| CULTURE |----####
def fill_raw_places(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:
    ''' Get the landmarks for a location
    Input: 	- location data
            - table_name: name of the table to insert the data into
            - db: Database objects
    Output: None
    '''
    # Get the directory of the current script and store api keys in list
    apikeys = []
    current_script_directory = os.path.dirname(os.path.abspath(__file__))
    path = "../../../../res/api_keys/geoapify_apikeys.txt"
    with open(os.path.join(current_script_directory, path), "r") as f:
        for line in f:
            apikeys.append(line.strip())
    i = 0  # Initialize API key index
    # Read categories
    path = "../../../../res/master_data/geoapify_rel_categories.csv"
    categories = pd.read_csv(os.path.join(current_script_directory, path))
    current_state = db.fetch_data(total_object="raw_places")

    locations = db.fetch_data(total_object="core_locations")

    MAX_RETRIES = 3  # Max number of retries
    WAIT_BASE = 1  # Base wait time in seconds
    WAIT_MULTIPLIER = 2  # Multiplier for exponential backoff
    call_count = 0
    MAX_CALLS = 25000  # Max number of calls per day

    for category in categories["place_category"]:
        # Create a set of for each location that has not been processed yet for the category
        missing_locations = locations[~locations["location_id"]
                                    .isin(current_state[current_state["place_category"] == category]
                                            ["location_id"])].reset_index(drop=True)
        if len(missing_locations) == 0:
            print(f"All locations have been processed for category {category}.")
            continue

        if call_count >= MAX_CALLS-1:
            print(f"\033[1m\033[91mLimits reached at category {category}. Trying with different API key or again tomorrow.\033[0m")
            break

        for location in missing_locations.iterrows():
            # Get places
            for retry in range(MAX_RETRIES):
                try:
                    places, call_count = get_places(
                        location=location[1],
                        category=category,
                        shape="circle",
                        apikey=apikeys[i],
                        call_count=call_count
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

    # Get current time for logging and return it
    end_datetime = datetime.datetime.now()

    return end_datetime



####----| WEATHER |----####
def fill_raw_weather_current_future(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:
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

    # Get current time for logging and return it
    end_datetime = datetime.datetime.now()

    return end_datetime


def fill_raw_weather_historical(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:
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

        # If any previous data is missing (e.g. data on 2022 but not on 2023), use the date of the first "gap"
        # Build list that contains all possible years and months from the maximum to the minimum
        possible_years_months = [(year, month) for year in range(2023, 2022-1, -1) for month in range(12, 0, -1)]

        # Check for each location if we have data on all possible years and months
        for location in current_state["location_id"].unique():
            existing_years_months = set(zip(
                current_state[current_state["location_id"] == location]["year"],
                current_state[current_state["location_id"] == location]["month"]
                ))
            missing_years_months = set(possible_years_months) - existing_years_months

            # Get maximum year and month for which we don't have data yet
            if missing_years_months:
                max_year_month = max(missing_years_months, key=lambda x: (x[0], x[1]))
                max_year = max_year_month[0] if max_year_month[1] != 12 else max_year_month[0] + 1
                max_month = max_year_month[1]+1 if max_year_month[1] != 12 else 1
            else:
                max_year = None
                max_month = None

            if max_year is not None:
                # Delete all other rows of this location except for the one with the maximum year and month
                current_state = current_state[(current_state["location_id"] != location) |
                                              ((current_state["location_id"] == location) & (current_state["year"] == max_year) & (current_state["month"] == max_month))]
            else:
                # Else leave the last period to be deleted later
                current_state = current_state[(current_state["location_id"] != location) |
                                              ((current_state["location_id"] == location) & (current_state["year"] == 2022) & (current_state["month"] == 1))]

        # If locations are totally missing in current_state, add them
        for _, row in locations.iterrows():
            if row["location_id"] not in current_state["location_id"].unique():
                current_state = pd.concat([
                    current_state,
                    pd.DataFrame({"location_id": row["location_id"], "year": 2024, "month": 1}, index=[0])
                    ],
                    ignore_index=True
                )

        # Order by latest year and month
        current_state = current_state.sort_values(by=["year", "month"], ascending=False)
        # Filter out all locations where we have data until January 2022
        current_state = current_state[~((current_state["year"] == 2022) & (current_state["month"] == 1))]

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

        # Get current time for logging and return it
        end_datetime = datetime.datetime.now()

        return end_datetime



####----| GEOGRAPHY |----####
def fill_raw_geography_coverage(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:
    ''' Get the land coverage for a location
    Input: 	- location data
            - table_name: name of the table to insert the data into
            - db: Database objects
    Output: None
    '''
    # Initialize Earth Engine
    ee.Initialize()

    # Get current location_ids with land coverage data
    current_state = db.fetch_data(table_name)

    # Get list of locations that are missing in the current state
    missing_locations = locations[~locations["location_id"].isin(current_state["location_id"])]

    # Get land coverage for each location
    for _, row in missing_locations.iterrows():

        print(f"Getting land coverage for {row['city']}, {row['country']}...")
        location_id = row["location_id"]
        geojson = json.loads(row["geojson"])

        land_coverage = get_land_coverage(location_id, geojson, "ESA")

        # If information could be found for this location, insert it into the database
        if len(land_coverage) > 0:
            db.insert_data(land_coverage, table_name, if_exists="append")

    # Get current time for logging and return it
    end_datetime = datetime.datetime.now()

    return end_datetime

####----| HEALTH |----####
# creates dataframe ready to be inserted into the raw_health_country table
def fill_raw_health(locations: pd.DataFrame, table_name: str, db: Database):

    # Run update on country information
    get_health_info()

    # Read in the csv file
    health_country_df = pd.read_csv("../../../res/master_data/health_info.csv")

    # If information could be found, insert it into the database
    if len(health_country_df) > 0:
        db.insert_data(health_country_df, table_name, if_exists="replace")

    # Get current time for logging and return it
    end_datetime = datetime.datetime.now()

    return end_datetime


####----| STEP 4: EXECUTE STEPS 1, 2 AND 3 |----####     
   
# Dictonary that maps names of database tables to functions which fill these tables with data
table_fill_function_dict = {
    #"raw_costs_numbeo": [fill_raw_costs_numbeo, 1],
    #"raw_safety_city": [fill_raw_safety_city, 2],
    #"raw_safety_country": [fill_raw_safety_country, 3],
    #"raw_places": [fill_raw_places, 4],
    # "raw_weather_current_future": [fill_raw_weather_current_future, 5],
    #"raw_weather_historical": [fill_raw_weather_historical, 6],
    #"raw_geography_coverage": [fill_raw_geography_coverage, 7],
    #"raw_accommodation_costs" : [fill_raw_accommodation_costs, 8],
    #"raw_reachability_air" : [fill_raw_reachability_air_par, 9],
    #"raw_reachability_land" : [fill_raw_reachability_land_par, 10],
    #"raw_health" : [fill_raw_health, 11]
    }

# List that consists of names of log tables that need to be created 
log_tables = ["log_history", "log_processes"]

# Dictonary that maps process_id to its fill_table function, its description and its turnus for the logging tables
table_process_id_dict = {
    1: ["raw_costs_numbeo", "Inserts numbeo cost data for given cities and countries.", 30],
    2: ["fill_raw_safety_city", "Inserts safety data for given cities.", 30],
    3: ["fill_raw_safety_country", "Inserts safety data for given countries.", 30],
    4: ["fill_raw_places", "Inserts culture data for given locations.", 30],
    5: ["raw_weather_current_future", "Inserts current and future weather data for given locations.", 30],
    6: ["raw_weather_historical", "Inserts historical weather data for given locations.", 30],
    7: ["fill_raw_geography", "Inserts geography data for given locations.", 30],
    8: ["fill_raw_accommodation", "Inserts accommodation data for given locations.", 30],
    9: ["fill_raw_reachability_air", "Inserts reachability data for given locations.", 30],
    10: ["fill_raw_reachability_land", "Inserts reachability data for given locations.", 30],
    11: ["fill_raw_health", "Inserts health data and travel information for all countries", 30]
}

# Connect to database
db = Database()
db.connect()
#print(db.fetch_data("raw_safety_country"))

# Create tables
create_raw_db_tables(db=db, table_names=table_fill_function_dict.keys(), drop_if_exists=True)
# Fill tables
fill_raw_db_tables(db=db, table_names=table_fill_function_dict.keys())

# Create logging
# create_log_db_tables(log_tables)
# fill_log_processes_db_table(table_process_id_dict.keys())

# Disconnect from database
db.disconnect()