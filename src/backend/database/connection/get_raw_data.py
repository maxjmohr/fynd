import pandas as pd
import os
import sys
import datetime
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import numpy as np

#add backend folder to sys.path so that .py-files from data directory can be imported as modules
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from data.costs import numbeoScraper
from data.safety_pipeline import create_country_safety_df
from data.safety_pipeline import create_city_safety_df
from data.culture import cultural_profile
from data import geography
from data import weather
from database.db_helpers import Database


# takes a list of table names and sets up these tables in the database
# names of tables must match names of sql-files in objects folder
def create_raw_db_tables(table_names):

    for table in table_names:
        db.create_db_object(table)

# takes a list of table names and sets up these tables in the database
# names of tables must match names of sql-files in objects folder
def create_log_db_tables(table_names):

    for table in table_names:
        db.create_db_object(table)

# creates dataframe ready to be inserted into the raw_costs_city table
def fill_raw_costs_city():
    ns = numbeoScraper()
    costs_city_df = ns.get_costs(by="city")

    return costs_city_df

# creates dataframe ready to be inserted into the raw_costs_country table
def fill_raw_costs_country():
    ns = numbeoScraper()
    costs_country_df = ns.get_costs(by="country")

    return costs_country_df

# creates dataframe ready to be inserted into the raw_safety_city table
def fill_raw_safety_city(location):
    safety_city_df = create_city_safety_df(location["city"])

    return safety_city_df

# creates dataframe ready to be inserted into the raw_safety_country table
def fill_raw_safety_country():
    safety_country_df = create_country_safety_df()

    return safety_country_df

# creates dataframe ready to be inserted into the raw_culture table
def fill_raw_culture(location):
    culture_df = cultural_profile(location["lat"]+","+location["lon"])
    culture_df = culture_df.convert_dtypes()

    return culture_df

# creates dataframe ready to be inserted into the raw_weather table
def fill_raw_weather(location):
    weather_params = {
	# Parameter for location
	"location": location["city"],
	# Parameters for all APIs
	"daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max", "apparent_temperature_min", "sunrise", "sunset",
		   "precipitation_sum", "rain_sum", "snowfall_sum", "wind_speed_10m_max"],
	"timezone": "auto",
	"models": "best_match",
	# Parameters for historical API
	"start_date": "2010-01-02", # Start in the beginning of 2010
	"end_date": date.today() - timedelta(days = 1), # excluding yesterday
	# Parameters for current and forecast API
	"past_days": 0,
	"forecast_days": 14
	}

    weather_df = weather.main(weather_params)
    weather_df.insert(0, 'weather_id', location["city"]+weather_df["date"].astype("str"))
    weather_df = weather_df.convert_dtypes()
    weather_df=weather_df[weather_df["weather_code"] != "<NA>"]

    return weather_df

# creates dataframe ready to be inserted into the raw_geography table
def fill_raw_geography(location):
    return None

# dictonary that maps names of database tables to functions which fill these tables with data and their process id
table_fill_function_dict = {
    #"raw_costs_city": [fill_raw_costs_city, 1],
    #"raw_costs_country": [fill_raw_costs_country, 2],
    "raw_safety_city": [fill_raw_safety_city, 3]
    #"raw_safety_country": [fill_raw_safety_country, 4]
    #"raw_culture" : [fill_raw_culture, 5],
    #"raw_weather" : [fill_raw_weather, 6]
    #"raw_geography" : [fill_raw_geography, 7]
                            }

# list that consists of names of log tables that need to be created 
log_tables = ["log_history", "log_processes"]

#dictonary that maps process_id to its fill_table function, its description and its turnus for the logging tables
table_process_id_dict = {
    1: ["fill_raw_costs_city", "Inserts cost data for given cities.", 30],
    2: ["fill_raw_costs_country", "Inserts cost data for given countries.", 30],
    3: ["fill_raw_safety_city", "Inserts safety data for given cities.", 30],
    4: ["fill_raw_safety_country", "Inserts safety data for given countries.", 30],
    5: ["fill_raw_culture", "Inserts culture data for given locations.", 30],
    6: ["fill_raw_weather", "Inserts weather data for given locations.", 30],
    7: ["fill_raw_geography", "Inserts geography data for given locations.", 30],
}


# calls fill-functions for individual tables and inserts data
def fill_raw_db_tables(table_names):

    # get list of locations from database
    locations_df = db.fetch_data("core_locations")

    #initialize table_df, exit_code, start_datetime and end_datetime to avoid duplicate code
    table_df = None
    exit_code = None
    start_datetime = None
    end_datetime = None

    # for each table (dimension) to be filled
    for table in table_names:
        try:
            # if table doesn't depend on locations from core_locations, insert data all at once
            if table == "raw_costs_city" or table == "raw_costs_country" or table == "raw_safety_country":
                #call fill-function, insert into table
                table_df = table_fill_function_dict[table][0]()
                start_datetime = datetime.datetime.now()
                db.insert_data(table_df, table)
                end_datetime = datetime.datetime.now()
            else:
                # for each location in core_locations
                for index, row in locations_df.iterrows():
                    #call fill-function for this location
                    table_df = table_fill_function_dict[table][0](row)
                    #insert if data for this location is available for this dimension, else print error message
                    if len(table_df) > 0:
                        start_datetime = datetime.datetime.now()
                        db.insert_data(table_df, table)
                        end_datetime = datetime.datetime.now()
                    else:
                        print("No data for table " + table + " for location " + row["city"] + ".")
            exit_code=0
        except Exception as error:
            print("Error when inserting into " + table + ":", type(error).__name__, "–", error)
            exit_code = 1
        finally:
            fill_log_history_db_table(process_id=table_fill_function_dict[table][1],
                                      start_datetime=start_datetime,
                                      status="Done",
                                      end_datetime=end_datetime,
                                      exit_code=exit_code)


# fills log_processes table in database with information on data insertion processes, takes process ids as input
def fill_log_processes_db_table(process_ids):

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
    
    #update log_processes with new last_exec and next_exec_scheduled times
    log_processes_df.loc[log_processes_df["process_id"]==process_id, "last_exec"] = last_exec
    log_processes_df.loc[log_processes_df["process_id"]==process_id, "next_exec_scheduled"] = next_exec_scheduled
    
    #insert data into log_history and log_processes tables
    db.insert_data(log_history_df, "log_history", updated_at=False)
    db.insert_data(log_processes_df, "log_processes", updated_at=False, if_exists='replace')


#fill_log_processes_db_table(table_process_id_dict.keys())
#conn, cur, engine = db_helpers.connect_to_db()

#res = db_helpers.fetch_data(engine, "raw_safety_country")
#print(res)
#db_helpers.disconnect_from_db(conn, cur, engine)

db = Database()
db.connect()
#print(db.fetch_data("log_history"))
#create_raw_db_tables(table_names=table_fill_function_dict.keys())
#fill_raw_db_tables(table_names=table_fill_function_dict.keys())
db.disconnect()

#create_log_db_tables(log_tables)
#fill_log_processes_db_table(table_process_id_dict.keys())