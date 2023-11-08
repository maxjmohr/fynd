import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from geopy.geocoders import Nominatim
from datetime import date, timedelta

params = {
	# Parameters for all APIs
	"daily": ["temperature_2m_max", "temperature_2m_min", "apparent_temperature_max", "apparent_temperature_min", "sunrise", "sunset",
		   "precipitation_sum", "rain_sum", "snowfall_sum", "wind_speed_10m_max"],
	"timezone": "auto",
	"models": "best_match",
	# Parameters for historical API
	"start_date": "2010-01-01",
	"end_date": date.today() - timedelta(days = 1), # ecluding yesterday
	# Parameters for current and forecast API
	"past_days": 0, # as the historical data of the past 5 days is not available via the other url (TBD)
	"forecast_days": 14
	}

def process_daily(response: openmeteo_requests, params: dict) -> pd.DataFrame:
	"""
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

def get_weather(location: str, params: dict) -> pd.DataFrame:
	"""
	Input: location (string)
	Output: weather data (pandas dataframe)
	"""
	# Get location coordinates
	geolocator = Nominatim(user_agent="Max Mohr")
	coor = geolocator.geocode(location)

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
		"past_days": params["past_days"], # as the historical data of the past 5 days is not available via the other url
		"forecast_days": params["forecast_days"]
	}
	response = openmeteo.weather_api(url, params=params_api)[0]

	# Process daily data
	daily_df = pd.concat([daily_df, process_daily(response, params)], ignore_index=True)

	# Output key information
	"""print(f"Location: {location}")
	print(f"Coordinates: {response.Latitude()}°E {response.Longitude()}°N")
	print(f"Elevation: {response.Elevation()} m asl")
	print(f"Timezone: {response.Timezone()} {response.TimezoneAbbreviation()}")
	print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()} s")"""
	print(daily_df)
   
	return daily_df

get_weather("Tuebingen", params)