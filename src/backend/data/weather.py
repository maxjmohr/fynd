import os
from datetime import date, timedelta
from geopy.geocoders import Nominatim
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

def read_weather_codes(path: str) -> pd.DataFrame:
	""" Reads in the official WMO weather interpretation codes (https://codes.wmo.int/bufr4/codeflag/_0-20-003)
	Input:  path
	Output: weather_codes (pandas dataframe)
	"""
	# Read the csv file
	weather_codes = pd.read_csv(path, usecols=["@notation", "rdfs:label"])
	# Clean the data
	weather_codes = weather_codes.rename(columns={"@notation": "weather_code", "rdfs:label": "weather_code_label"})
	weather_codes["weather_code_label"] = weather_codes["weather_code_label"].str.replace("@en", "")
	weather_codes["weather_code_label"] = weather_codes["weather_code_label"].str[1:-1]

	return weather_codes

def process_daily(response: openmeteo_requests, params: dict) -> pd.DataFrame:
	""" Processes daily weather data and returns a df
	Input:  - API response (openmeteo_requests)
			- Requested dimensions (dict)
	Output: API output (pandas dataframe)
	"""
	# Process daily data
	daily = response.Daily()

	# Setup daily output
	daily_data = {"date": pd.date_range(
		start = pd.to_datetime(daily.Time(), unit = "s"),
		end = pd.to_datetime(daily.TimeEnd(), unit = "s"),
		freq = pd.Timedelta(seconds = daily.Interval()),
		inclusive = "left"
	).date}

	# The order of variables is the same as requested
	for i,var in enumerate(params["daily"]): 
		daily_data[var] = daily.Variables(i).ValuesAsNumpy()

	return pd.DataFrame(data = daily_data)

def main(params: dict) -> pd.DataFrame:
	""" Unites historical, current and future weather data
	Input: 	parameters (dict)
	Output: weather data (pandas dataframe)
	"""
	# Get location coordinates
	geolocator = Nominatim(user_agent="Max Mohr")
	coor = geolocator.geocode(params["location"])

	# Setup the Open-Meteo API client with cache and retry on error
	cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
	retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
	openmeteo = openmeteo_requests.Client(session=retry_session)

	###--- Get historical weather data since 2010-01-01 ---###
	url = "https://archive-api.open-meteo.com/v1/archive"
	params_api = {
		"latitude": coor.latitude,
		"longitude": coor.longitude,
		"daily": params["daily"],
		"timezone": params["timezone"],
		"models": params["models"],
		"start_date": params["start_date"],
		"end_date": params["end_date"]
	}
	response = openmeteo.weather_api(url, params=params_api)[0]

	# Process daily data
	daily_df = process_daily(response, params)

	###--- Get current, future and (perhaps) historical weather data ---###
	url = "https://api.open-meteo.com/v1/forecast"
	params_api = {
		"latitude": coor.latitude,
		"longitude": coor.longitude,
		"daily": params["daily"],
		"timezone": params["timezone"],
		"models": params["models"],
		"past_days": params["past_days"],
		"forecast_days": params["forecast_days"]
	}
	response = openmeteo.weather_api(url, params=params_api)[0]

	# Process daily data
	daily_df = pd.concat([daily_df, process_daily(response, params)], ignore_index=True)

	###--- Add weather code labels ---###
	# Get the directory of the current script
	current_script_directory = os.path.dirname(os.path.abspath(__file__))

	# Merge the weather codes to the dataframe
	weather_codes = read_weather_codes(os.path.join(current_script_directory, "../../../res/master_data/weather_codes.csv"))
	daily_df = daily_df.merge(weather_codes, on="weather_code", how="left")

	# Output key information
	"""print(f"Location: {location}")
	print(f"Coordinates: {response.Latitude()}°E {response.Longitude()}°N")
	print(f"Elevation: {response.Elevation()} m asl")
	print(f"Timezone: {response.Timezone()} {response.TimezoneAbbreviation()}")
	print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()} s")"""
   
	return daily_df

params = {
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

if __name__ == "__main__":
    main(params)