import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database

import calendar
from datetime import datetime
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


class WeatherScores:
    "Class for calculating weather scores"
    def __init__(self, db:Database) -> None:
        ''' Initialize the class
        Input:  db: Database object
        Output: None
        '''
        self.db = db


    def prep_data(self, year:int) -> pd.DataFrame:
        ''' Fetch the data
        Input:  - db
                - year
        Output: weather data
        '''
        # Fetch the data
        data = self.db.fetch_data(total_object="raw_weather_historical")

        # Aggregate per location and month
        data = data.pivot_table(index=["location_id", "month"],
                                aggfunc={"temperature_max": "mean",
                                         "temperature_min": "mean",
                                         "sunshine_duration": "mean",
                                         "daylight_duration": "mean",
                                         "precipitation_duration": "mean",
                                         "precipitation_sum": "mean",
                                         "rain_sum": "mean",
                                         "snowfall_sum": "mean",
                                         "wind_speed_max": "mean"}) \
            .reset_index(inplace=False)

        # Rename columns
        new_names = {
            "temperature_max": "Maximum temperature",
            "temperature_min": "Minimum temperature",
            "sunshine_duration": "Sunshine duration",
            "daylight_duration": "Daylight duration",
            "precipitation_duration": "Precipitation duration",
            "precipitation_sum": "Precipitation amount",
            "rain_sum": "Rain amount",
            "snowfall_sum": "Snowfall amount",
            "wind_speed_max": "Maximum wind speed"
        }
        data = data.rename(columns=new_names)

        # Duplicate month columns for end_date
        data["end_date"] = data["month"]
        # Rename month to start_date
        data = data.rename(columns={"month": "start_date"})

        # Add start_date and end_date
        data["start_date"] = data["start_date"] \
            .map(lambda x: datetime(year, x, 1).date())
        data["end_date"] = data["end_date"] \
            .map(lambda x: datetime(year, x, calendar.monthrange(year, x)[1]).date())

        # Bring into long format
        value_vars = list(new_names.values())
        data = data.melt(id_vars=["location_id", "start_date", "end_date"], 
                 value_vars=value_vars,
                 var_name="dimension_id", 
                 value_name="raw_value")

        # Get dimension_id for each column
        sql = """
            SELECT dimension_id, dimension_name
            FROM core_dimensions
            WHERE category_id = 2
            """
        dimension_map = self.db.fetch_data(sql=sql)
        dimension_map = {row["dimension_name"]: row["dimension_id"] for _, row in dimension_map.iterrows()}
        data["dimension_id"] = data["dimension_id"] \
            .map(dimension_map)

        # Normalize scores between 0 and 1 using Min-Max scaling for each dimension
        for dimension_id in data["dimension_id"].unique():
            data.loc[data["dimension_id"] == dimension_id, "score"] = \
                MinMaxScaler(feature_range=(0, 1)).fit_transform(
                    data.loc[data["dimension_id"] == dimension_id, ["raw_value"]]
                )

        # Add category_id
        data["category_id"] = self.db.fetch_data(sql="SELECT category_id FROM core_categories WHERE category_id = 2").iloc[0, 0]

        # Add ref_start_location_id
        data["ref_start_location_id"] = -1

        return data[["location_id", "category_id", "dimension_id", "start_date", "end_date", "ref_start_location_id", "score", "raw_value"]]


    def get(self) -> pd.DataFrame:
        ''' Get the weather scores
        Input:  None
        Output: weather scores
        '''
        # Get current and next year
        years = (datetime.now().year, datetime.now().year+1)

        # Get the data for the current and next year
        current = self.prep_data(year=years[0])
        next = self.prep_data(year=years[1])

        # Merge the data
        return pd.concat([current, next], axis=0)

"""
# Connect to the database
db = Database()
db.connect()

data = WeatherScores(db).get()

# Display the result
print(data[["location_id", "category_id", "dimension_id", "start_date", "end_date", "ref_start_location_id", "score", "raw_value"]].sort_values(by="score", ascending=False).head(50))

db.disconnect()
"""