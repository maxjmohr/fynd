import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from data.costs import numbeoScraper
#from data.safety import create_country_safety_df
#from data.safety import create_city_safety_df
from data.geography import get_land_coverage
#from data.places import get_places
from data.weather import SingletonHistWeather, SingletonCurrFutWeather
from data.accomodations import accomodations_main
from data.reachability import process_location_land_reachability, process_location_air_reachability
from database.db_helpers import Database
import datetime
from dateutil.relativedelta import relativedelta
import ee
import json
import numpy as np
import pandas as pd
import random
import time

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

    ####----| STEP 4: EXECUTE STEPS 1, 2 AND 3 |----####   

def fill_raw_accommodation():

    accomodations_main()

    return None


def fill_raw_reachability_land(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:

    # iterate over locations
    for _, loc in locations.iterrows():

        # module function returns a dataframe with combinations for all start locations and the current location
        loc_land_reachability_df = process_location_land_reachability(loc, start_refs)

        # insert that into "table_name" if it is not empty
        if len(loc_land_reachability_df) > 0:
            db.insert_data(loc_land_reachability_df, table_name, if_exists='append')

    end_datetime = datetime.datetime.now()

    return end_datetime 


def fill_raw_reachability_air(locations: pd.DataFrame, table_name: str, db: Database) -> datetime.datetime:

    locations = locations[~locations['city'].isin(["Shkoder", "Kruje", "Korçë", "Fier",
                                                   "Berat", "Bashkia Durrës"])]

    if os.path.exists("./res/master_data/location_rename.json"):
        with open("./res/master_data/location_rename.json", "r", encoding="utf-8") as f:
            location_rename = json.load(f)

    locations = locations[~locations['country'].isin(["Belarus", "Russia", "Iran"])]
    locations.loc[locations['location_id'] == 206579565, 'city'] = "Hong Kong"
    locations.loc[locations['location_id'] == 206579565, 'country'] = "Hong Kong"  
    locations['city'] = locations[['city', 'country']].apply(lambda x: location_rename[f"{x['city']}, {x['country']}"] if f"{x['city']}, {x['country']}" in location_rename.keys() else x['city'],  axis=1)

    # iterate over locations
    for _, loc in locations.iterrows():

        # module function returns a dataframe with combinations for all start locations and the current location
        loc_air_reachability_df = process_location_air_reachability(loc, start_refs)

        # insert that into "table_name" if it is not empty
        if len(loc_air_reachability_df) > 0:
            db.insert_data(loc_air_reachability_df, table_name, if_exists='append')

    end_datetime = datetime.datetime.now()

    return end_datetime


# Dictonary that maps names of database tables to functions which fill these tables with data
table_fill_function_dict = {
    #"raw_costs_numbeo": [fill_raw_costs_numbeo, 1],
    #"raw_safety_city": [fill_raw_safety_city, 2],
    #"raw_safety_country": [fill_raw_safety_country, 3],
    #raw_places": [fill_raw_places, 4],
    # "raw_weather_current_future": [fill_raw_weather_current_future, 5],
    #"raw_weather_historical": [fill_raw_weather_historical, 6],
    #"raw_geography_coverage": [fill_raw_geography_coverage, 7],
    #"raw_accommodation" : [fill_raw_accommodation, 8],
    #"raw_reachability_air" : [fill_raw_reachability_air, 9],
    "raw_reachability_land" : [fill_raw_reachability_land, 10]
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
    10: ["fill_raw_reachability_land", "Inserts reachability data for given locations.", 30]
}

# Connect to database
db = Database()
db.connect()

# define start references in global scope for reachability
start_refs = db.fetch_data("core_ref_start_locations")

# Create tables
#create_raw_db_tables(db=db, table_names=table_fill_function_dict.keys(), drop_if_exists=False)
# Fill tables
fill_raw_db_tables(db=db, table_names=table_fill_function_dict.keys())

# Create logging
# create_log_db_tables(log_tables)
# fill_log_processes_db_table(table_process_id_dict.keys())

# Disconnect from database
db.disconnect()