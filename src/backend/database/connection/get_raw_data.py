import pandas as pd
import os
import sys
from datetime import date, timedelta

#add backend folder to sys.path so that .py-files from data directory can be imported as modules
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from data.safety_pipeline import create_country_safety_df
from data.culture import cultural_profile
from data.costs import numbeoScraper
from data import geography
from data import weather
from database.internal.get_locations import LocationMasterData
from database import db_helpers


dummy_destinations = [["Tübingen", "Germany"]]

""" ns = numbeoScraper()
costs_country_df = ns.get_costs(by="country")
costs_city_df = ns.get_costs(by="city")
safety_df = create_country_safety_df() """


weather_params = {
	# Parameter for location
	"location": "Tuebingen",
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

for dest in dummy_destinations:
    weather_df = weather.main(weather_params)
    weather_df.insert(0, 'weather_id', dest[0]+weather_df["date"].astype("str"))
    weather_df = weather_df.convert_dtypes()
    print(weather_df.columns)
    print(weather_df.iloc[0])
    print(weather_df.dtypes)
    """ data, geo_json = LocationMasterData(city=dest[0], country=dest[1], shape="polygon").get_all()
    culture_df = cultural_profile(data["lat"]+","+data["lon"])
    culture_df = culture_df.drop("Unnamed: 0", axis=1)
    culture_df = culture_df.convert_dtypes() """

""" geography_params = {
    # Parameters for get_geojson()
    "city": dummy_destinations[0][0],
    "country": dummy_destinations[0][1],
    "shape_geojson": "polygon",
    "radius_geojson": 5,
    # Parameters for get_land_coverage()
    "map": "ESA", # and city
    # Parameters for get_landmarks()
    "shape_landmarks": "box",
    "radius_landmarks": 13000
}

geography.main(params=geography_params) """



#data, geo_json = LocationMasterData(city="Tuebingen", country="Germany", shape="polygon").get_all()

conn, cur, engine = db_helpers.connect_to_db()
db_helpers.create_db_object(conn, cur, "raw_weather")
db_helpers.insert_data(engine, weather_df, "raw_weather")
""" db_helpers.create_db_object(conn, cur, "raw_culture")
db_helpers.insert_data(engine, culture_df, "raw_culture")

db_helpers.create_db_object(conn, cur, "raw_costs_country")
db_helpers.insert_data(engine, costs_country_df, "raw_costs_country")

db_helpers.create_db_object(conn, cur, "raw_costs_city")
db_helpers.insert_data(engine, costs_city_df, "raw_costs_city")

db_helpers.create_db_object(conn, cur, "raw_safety")
db_helpers.insert_data(engine, safety_df, "raw_safety") """


res = db_helpers.fetch_data(engine, "raw_weather")
print(res)
db_helpers.disconnect_from_db(conn, cur, engine)

