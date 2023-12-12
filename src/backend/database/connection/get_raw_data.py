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
import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd

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
    
    # Initialize table_df, exit_code, start_datetime and end_datetime to avoid duplicate code
    table_df = None
    exit_code = None
    start_datetime = None
    end_datetime = None
    
    # Fill each table
    for table in table_names:
        try:
            # If table doesn't depend on locations from core_locations, insert data all at once
            if table == "raw_safety_country":
                #call fill-function, insert into table
                table_df = table_fill_function_dict[table][0]()
                start_datetime = datetime.datetime.now()
                db.insert_data(table_df, table)
                end_datetime = datetime.datetime.now()
                
            else: 
                # Call the fill function
                table_fill_function_dict[table][0](locations_df, table, db)
                
                """ TO-DO: THE INSERT HAPPENS IN THE FILL FUNCTIONS
                if len(table_df) > 0:
                        start_datetime = datetime.datetime.now()
                        db.insert_data(table_df, table)
                        end_datetime = datetime.datetime.now()
                    else:
                        print("No data for table " + table + " for location " + row["city"] + ".")
                """
            exit_code = 0
            
        except Exception as error:
            print("Error when inserting into " + table + ":", type(error).__name__, "–", error)
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
def create_log_db_tables(table_names):

    for table in table_names:
        db.create_db_object(table)
        
        
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



####----| STEP 3: FILL TABLES |----####

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
def fill_raw_safety_country():
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



####----| STEP 4: EXECUTE STEPS 1, 2 AND 3 |----####    

# Dictonary that maps names of database tables to functions which fill these tables with data
table_fill_function_dict = {
    #"raw_costs_numbeo": [fill_raw_costs_numbeo, 1],
    #"raw_safety_city": [fill_raw_safety_city, 2],
    #"raw_safety_country": [fill_raw_safety_country, 3],
    #"raw_culture": [fill_raw_culture, 4],
    # "raw_weather_current_future": [fill_raw_weather_current_future, 5],
    "raw_weather_historical": [fill_raw_weather_historical, 6],
    #"raw_geography": [fill_raw_geography 7]
    }

# List that consists of names of log tables that need to be created 
log_tables = ["log_history", "log_processes"]

# Dictonary that maps process_id to its fill_table function, its description and its turnus for the logging tables
table_process_id_dict = {
    1: ["raw_costs_numbeo", "Inserts numbeo cost data for given cities and countries.", 30],
    2: ["fill_raw_safety_city", "Inserts safety data for given cities.", 30],
    3: ["fill_raw_safety_country", "Inserts safety data for given countries.", 30],
    4: ["fill_raw_culture", "Inserts culture data for given locations.", 30],
    5: ["raw_weather_current_future", "Inserts current and future weather data for given locations.", 30],
    6: ["raw_weather_historical", "Inserts historical weather data for given locations.", 30],
    7: ["fill_raw_geography", "Inserts geography data for given locations.", 30],
}

# Connect to database
db = Database()
db.connect()

# Create tables
# create_raw_db_tables(db=db, table_names=table_fill_function_dict.keys(), drop_if_exists=False)
# Fill tables
fill_raw_db_tables(db=db, table_names=table_fill_function_dict.keys())

# Create logging
# create_log_db_tables(log_tables)
# fill_log_processes_db_table(table_process_id_dict.keys())

# Disconnect from database
db.disconnect()