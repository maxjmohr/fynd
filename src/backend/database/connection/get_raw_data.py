import pandas as pd
import os
import sys
from datetime import date, timedelta

#add backend folder to sys.path so that .py-files from data directory can be imported as modules
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from data.costs import numbeoScraper
from data.safety_pipeline import create_country_safety_df
from data.safety_pipeline import create_city_safety_df
from data.culture import cultural_profile
from data import geography
from data import weather
from database.internal.get_locations import LocationMasterData
from database import db_helpers


dummy_destinations = [["Tübingen", "Germany"]]

# takes a list of table names and sets up these tables in the database
# names of tables must match names of sql-files in objects folder
def create_raw_db_tables(table_names):
    conn, cur, engine = db_helpers.connect_to_db()

    for table in table_names:
        db_helpers.create_db_object(conn, cur, table)

    db_helpers.disconnect_from_db(conn, cur, engine)

# creates dataframe ready to be inserted into the raw_costs_city table
def fill_raw_costs_city(location):
    ns = numbeoScraper()
    costs_city_df = ns.get_costs(by="city")

    return costs_city_df

# creates dataframe ready to be inserted into the raw_costs_country table
def fill_raw_costs_country(location):
    ns = numbeoScraper()
    costs_country_df = ns.get_costs(by="country")

    return costs_country_df

# creates dataframe ready to be inserted into the raw_safety_city table
def fill_raw_safety_city(location):
    safety_city_df = create_city_safety_df(location["city"])

    return safety_city_df

# creates dataframe ready to be inserted into the raw_safety_country table
def fill_raw_safety_country(location):
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

# dictonary that maps names of database tables to functions which fill these tables with data
table_fill_function_dict = {
    "raw_costs_city": fill_raw_costs_city,
    "raw_costs_country": fill_raw_costs_country,
    "raw_safety_city": fill_raw_safety_city,
    "raw_safety_country": fill_raw_safety_country,
    "raw_culture" : fill_raw_culture,
    "raw_weather" : fill_raw_weather
    #"raw_geography" : fill_raw_geography
                            }

# calls fill-functions for individual tables and inserts data
def fill_raw_db_tables(table_names):
    conn, cur, engine = db_helpers.connect_to_db()

    # get list of locations from database
    locations_df = db_helpers.fetch_data(engine, "core_locations")

    # for each location
    for index, row in locations_df.iterrows():
        # for each table to be filled
        for table in table_names:
            #call fill-function for this location
            table_df = table_fill_function_dict[table](row)
            if len(table_df) > 0:
                db_helpers.insert_data(engine, table_df, table)
            else:
                print("Found no data for table " + table + " for location " + row["city"] + ".")
    db_helpers.disconnect_from_db(conn, cur, engine)


#conn, cur, engine = db_helpers.connect_to_db()

#location_df = db_helpers.fetch_data(engine, "core_locations")

#db_helpers.disconnect_from_db(conn, cur, engine)

create_raw_db_tables(table_names=table_fill_function_dict.keys())
fill_raw_db_tables(table_names=table_fill_function_dict.keys())