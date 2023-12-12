from datetime import date
import os
import openmeteo_requests
import pandas as pd
import requests_cache
import sys
import time
from retry_requests import retry

class OpenMeteoWeather:
	''' Class for the Open-Meteo API
	Weight per call: #locations * (#days/14) * (#params/10) -> 1 call = 1 location, 2 weeks, 1 param
	Call limits:    - daily: 10,000 calls
					- hourly: 5,000 calls
					- minute: 600 calls
	'''
	def __init__(self, params: dict, time:str) -> None:
		'''Initialize the class
		Input:  - params
				- time
		'''
		self.params = params
		self.time = time
		if self.time != "historical" and self.time != "current_future":
			raise ValueError("Time must be either 'historical' or 'current_future'")
		self.call_count = 0
		self.call_day = None


	def read_weather_codes(self) -> pd.DataFrame:
		''' Reads in the official WMO weather interpretation codes (https://codes.wmo.int/bufr4/codeflag/_0-20-003)
		Input:  None
		Output: weather codes
		'''
		# Read the csv file
		current_script_directory = os.path.dirname(os.path.abspath(__file__))
		path = os.path.join(current_script_directory, "../../../res/master_data/weather_codes.csv")
		weather_codes = pd.read_csv(path, usecols=["@notation", "rdfs:label"])

		# Clean the data
		weather_codes = weather_codes.rename(columns={"@notation": "weather_code", "rdfs:label": "weather_code_label"})
		weather_codes["weather_code_label"] = weather_codes["weather_code_label"].str.replace("@en", "")
		weather_codes["weather_code_label"] = weather_codes["weather_code_label"].str[1:-1]
		
		return weather_codes
	

	def call_limit(self, call_count_initial:int = 0, call_day_initial:date = None) -> None:
		''' Checks the call limit and sleeps if necessary
		Input:  - self.time
				- call_count: number of calls made today
				- call_day: date of the last call
		Output: None
		'''
		# Reset the call count if it is a new day
		if self.call_day != date.today() or self.call_day == None:
			self.call_count = 0
			self.call_day = date.today()

		# Calls are weighted differently
		if self.time == "historical":
			self.call_count += 2
		elif self.time == "current_future":
			self.call_count += 1

		# Minutely limit
		time.sleep((60/(600/2))+0.1)  # 60 seconds / (600 max calls per minute / 2 calls per iteration) + 0.1 seconds to be safe

		# Hourly limit
		if self.call_count >= 5000:
			# Sleep for one hour
			print('\033[1m\033[91mMore than 5,000 API calls for this day. Sleeping for one hour to avoid being blocked.\033[0m')
			time.sleep(3600)

		# Daily limit
		elif self.call_count >= 10000:
			print('\033[1m\033[91mMore than 10,000 API calls for this day. Please try again on a new day to avoid being blocked.\033[0m')
			sys.exit()


	def process_data(self, response: openmeteo_requests) -> pd.DataFrame:
		''' Processes daily weather data and returns a df
		Input:  - Requested dimensions (self.params)
				- API response (openmeteo_requests)
		Output: API output (pandas dataframe)
		'''
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
		for i,var in enumerate(self.params["daily"]): 
			daily_data[var] = daily.Variables(i).ValuesAsNumpy()

		# Turn the dictionary into a dataframe
		daily_data = pd.DataFrame(data = daily_data)

		# Merge the weather codes to the dataframe
		weather_codes = self.read_weather_codes()
		daily_data = daily_data.merge(weather_codes, on="weather_code", how="left")

		# Rename columns
		daily_data = daily_data.rename(columns={"temperature_2m_max": "temperature_max",
											  	"temperature_2m_min": "temperature_min",
												"precipitation_hours": "precipitation_duration",
												"wind_speed_10m_max": "wind_speed_max"})
		
		# Turn seconds columns into hours
		daily_data["sunshine_duration"] = daily_data["sunshine_duration"] / 60 / 60
		daily_data["daylight_duration"] = daily_data["daylight_duration"] / 60 / 60

		# Get location data and monmth
		daily_data["location_id"] = self.location_id
		daily_data["month"] = pd.to_datetime(daily_data['date']).dt.month

		if self.time == "historical":
			# Get further data to aggreagate on
			daily_data["year"] = pd.to_datetime(daily_data['date']).dt.year

			# Create a pivot table to get averages for numerical columns and mode for text columns
			daily_data = daily_data.pivot_table(index=["location_id", "year", "month"],
													aggfunc={"temperature_max": "mean",
															"temperature_min": "mean",
															"sunshine_duration": "mean",
															"daylight_duration": "mean",
															"precipitation_duration": "mean",
															"precipitation_sum": "mean",
															"rain_sum": "mean",
															"snowfall_sum": "mean",
															"wind_speed_max": "mean",
															"weather_code_label": lambda x: x.mode().iloc[0]}).reset_index(inplace=False)

			# Reorder columns
			daily_data = daily_data[["location_id", "year", "month", "temperature_max", "temperature_min",
							"sunshine_duration", "daylight_duration", "precipitation_duration",
							"precipitation_sum", "rain_sum",  "snowfall_sum", "wind_speed_max", "weather_code_label"]]
			
		elif self.time == "current_future":
			# Reorder columns
			daily_data = daily_data[["location_id", "date", "month", "temperature_max", "temperature_min",
							"sunshine_duration", "daylight_duration", "precipitation_duration",
							"precipitation_sum", "rain_sum", "snowfall_sum", "wind_speed_max", "weather_code_label"]]
		
		return daily_data


	def get_data(self, location_id:int, lat:float, lon:float) -> pd.DataFrame:
		''' Unites historical, current and future weather data
		Input: 	- self.parameters
				- location_id
				- lat
				- lon
		Output: - historical weather data
				- current and future weather data
		'''
		# Specify the location
		self.location_id = location_id

		# Setup the Open-Meteo API client with cache and retry on error
		cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
		retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
		openmeteo = openmeteo_requests.Client(session=retry_session)

		if self.time == "historical":
			###-------| Get historical weather data |-------###
			url = "https://archive-api.open-meteo.com/v1/archive"
			params_api = {
				"latitude": lat,
				"longitude": lon,
				"daily": self.params["daily"],
				"timezone": self.params["timezone"],
				"models": self.params["models"],
				"start_date": self.params["start_date"],
				"end_date": self.params["end_date"]
			}
			response = openmeteo.weather_api(url, params=params_api)[0]

			# Call parameters
			self.call_limit()

			# Process daily data and aggregate it
			data = self.process_data(response)

		elif self.time == "current_future":
			###-------| Get current and future weather data |-------###
			url = "https://api.open-meteo.com/v1/forecast"
			params_api = {
				"latitude": lat,
				"longitude": lon,
				"daily": self.params["daily"],
				"timezone": self.params["timezone"],
				"models": self.params["models"],
				"past_days": self.params["past_days"],
				"forecast_days": self.params["forecast_days"]
			}
			response = openmeteo.weather_api(url, params=params_api)[0]

			# Call parameters
			self.call_limit()

			# Process daily data
			data = self.process_data(response)
	
		return data


# Subclasses to create singletons
class SingletonHistWeather(OpenMeteoWeather):
	"Singleton class for the Open-Meteo historical weather API"
	_instance = None

	def __new__(cls, params, time):
		if cls._instance is None:
			cls._instance = super(SingletonHistWeather, cls).__new__(cls)
			OpenMeteoWeather.__init__(cls._instance, params, time)
		return cls._instance


class SingletonCurrFutWeather(OpenMeteoWeather):
	"Singleton class for the Open-Meteo current and future weather API"
	_instance = None

	def __new__(cls, params, time):
		if cls._instance is None:
			cls._instance = super(SingletonCurrFutWeather, cls).__new__(cls)
			OpenMeteoWeather.__init__(cls._instance, params, time)
		return cls._instance
	
"""
weather_params = {
	# Parameters for all APIs
	"daily": ["weather_code", "temperature_2m_max", "temperature_2m_min",
		"sunshine_duration", "daylight_duration", "precipitation_hours", "precipitation_sum", "rain_sum", "snowfall_sum", "wind_speed_10m_max"],
	"timezone": "auto",
	"models": "best_match",
	# Parameters for historical API
	"start_date": "2018-01-02",
	"end_date": "2023-01-01",
	# Parameters for historical API
	"start_date": "2022-10-02",
	"end_date": "2022-10-30"
	}
"""

"""
data = OpenMeteoWeather(weather_params, "historical").get_data(0, 34.5260109, 69.1776838)
print(data)
"""

"""
cfw = CurrentFutureWeather(params=weather_params, time="current_future")
print(cfw.call_count)
print(cfw.call_day)
"""