import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from geopy.geocoders import Nominatim

def get_weather(location: str):
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

	# Make sure all required weather variables are listed here
	url = "https://api.open-meteo.com/v1/forecast"
	params = {
		"latitude": coor.latitude,
		"longitude": coor.longitude,
		"daily": ["temperature_2m_max", "temperature_2m_min"],
		"timezone": "auto",
		"past_days": 5, # as the historical data of the past 5 days is not available via the other url
		"forecast_days": 14,
		"models": "best_match"
	}
	response = openmeteo.weather_api(url, params=params)[0]

	url_hist = "https://archive-api.open-meteo.com/v1/archive"
	params = {
		"latitude": coor.latitude,
		"longitude": coor.longitude,
		"start_date": "2010-01-01",
		"end_date": "2023-11-01",
		"daily": ["temperature_2m_max", "temperature_2m_min"],
		"timezone": "auto",
		"models": "best_match"
	}
	response_hist = openmeteo.weather_api(url_hist, params=params)[0]

	# Output key information
	"""print(f"Location: {location}")
	print(f"Coordinates: {response.Latitude()}°E {response.Longitude()}°N")
	print(f"Elevation: {response.Elevation()} m asl")
	print(f"Timezone: {response.Timezone()} {response.TimezoneAbbreviation()}")
	print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()} s")"""

	# Process daily and monthly data
	daily = response.Daily()
	print(daily)

	# Setup daily output
	daily_data = {"date": pd.date_range(
		start = pd.to_datetime(daily.Time(), unit = "s"),
		end = pd.to_datetime(daily.TimeEnd(), unit = "s"),
		freq = pd.Timedelta(seconds = daily.Interval()),
		inclusive = "left"
	)}

	# The order of variables is the same as requested
	for i,var in enumerate(params["daily"]): 
		daily_data[var] = daily.Variables(i).ValuesAsNumpy()

	daily_dataframe = pd.DataFrame(data = daily_data)
	print(daily_dataframe)
    
	return daily_dataframe

get_weather("Tuebingen")