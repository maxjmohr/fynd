import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from data.costs import numbeoScraper
#from data.safety import create_country_safety_df
#from data.safety import create_city_safety_df
#from data.geography import get_land_coverage
#from data.places import get_places
#from data.weather import SingletonHistWeather, SingletonCurrFutWeather
from data.accomodations import generate_periods, process_period
from data.reachability import (process_location_land_reachability, 
                               process_location_air_reachability, 
                               fill_reachibility_table)
import datetime
from database.db_helpers import Database
from multiprocessing import Pool
from geopy.distance import geodesic
from dateutil.relativedelta import relativedelta
import ee
import json
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

    ####----| STEP 4: EXECUTE STEPS 1, 2 AND 3 |----####   


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

    end_datetime = datetime.datetime.now()

    return end_datetime


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


if __name__ == '__main__':

    # Dictonary that maps names of database tables to functions which fill these tables with data
    table_fill_function_dict = {
        #"raw_costs_numbeo": [fill_raw_costs_numbeo, 1],
        #"raw_safety_city": [fill_raw_safety_city, 2],
        #"raw_safety_country": [fill_raw_safety_country, 3],
        #raw_places": [fill_raw_places, 4],
        # "raw_weather_current_future": [fill_raw_weather_current_future, 5],
        #"raw_weather_historical": [fill_raw_weather_historical, 6],
        #"raw_geography_coverage": [fill_raw_geography_coverage, 7],
        #"raw_accommodation_costs" : [fill_raw_accommodation_costs, 8],
        #"raw_reachability_air" : [fill_raw_reachability_air_par, 9],
        "raw_reachability_land" : [fill_raw_reachability_land_par, 10]
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
    #create_raw_db_tables(db=db, table_names=table_fill_function_dict.keys(), drop_if_exists=True)

    # Fill tables
    fill_raw_db_tables(db=db, table_names=table_fill_function_dict.keys())

    # Create logging
    # create_log_db_tables(log_tables)
    # fill_log_processes_db_table(table_process_id_dict.keys())

    # Disconnect from database
    db.disconnect()