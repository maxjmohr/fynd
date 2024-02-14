import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

class CultureScores:
    "Class to calculate the geography scores of a city"
    def __init__(self, db:Database) -> None:
        ''' Initialize the class
        Input:  db: Database object
        Output: None
        '''
        self.db = db


    @staticmethod
    def map_place_to_dimension(category:str) -> int:
        ''' Map the place_category to the correct dimension id
        Input:  category: category of the place
        Output: dimension_id: dimension_id of the place
        '''
        category = category.lower()
    
        category_mapping = {
            ".restaurant": 31,
            "catering.ice_cream": 31,
            ".food_court": 31,
            ".fast_food": 32,
            ".bar": 33,
            ".pub": 33,
            ".biergarten": 33,
            ".taproom": 33,
            ".cafe": 34,
            "entertainment": 35,
            ".culture": 35,
            ".museum": 35,
            ".planetarium": 35,
            ".cinema": 35,
            ".zoo": 36,
            ".aquarium": 36,
            ".theme_park": 36,
            ".water_park": 36,
            ".activity_park": 36,
            ".amusement_arcade": 36,
            ".escape_game": 36,
            ".miniature_golf": 36,
            ".bowling_alley": 36,
            ".flying_fox": 36,
            "leisure": 36,
            ".nightclub": 36,
            "natural": 37,
            "natural.": 37,
            "national_park": 37,
            "beach": 37,
            "ski": 37,
            "tourism.": 38,
        }
        for key, value in category_mapping.items():
            if key in category:
                return value

        return print(f"{datetime.now()} - Category {category} could not be mapped.")


    def get(self) -> pd.DataFrame:
        ''' Get the scores of a location
        Input:  db
        Output: scores: scores of a location
        '''
        # Fetch the found places
        sql = """
            SELECT *
            FROM raw_places
            WHERE place_name != 'None found'
        """
        data = self.db.fetch_data(sql=sql)

        # Map the place_category to the correct dimension_id
        data["dimension_id"] = data["place_category"].apply(self.map_place_to_dimension)

        # Drop duplicate places for the same location_id and dimension_id
        # Keep those where place_category is longer string to keep the more detailed categories
        data = data.assign(place_category_length=data['place_category'].str.len()) \
            .sort_values(by="place_category_length", ascending=False,) \
            .drop_duplicates(subset=["location_id", "dimension_id", "place_name"])

        # Per location_id and dimension_id, count distinct places
        data = data.groupby(["location_id", "dimension_id"])["dimension_id"] \
            .count() \
            .reset_index(name="score")

        # If a location_id and dimension_id combination is not present, add a dummy entry
        for location_id, dimension_id in zip(data["location_id"].unique(), data["dimension_id"].unique()):
            if dimension_id not in data[data["location_id"] == location_id]["dimension_id"].values:
                data = data.append({"location_id": location_id, "dimension_id": dimension_id, "score": 0.}, ignore_index=True)

        # Convert score to log scale
        data["score"] = np.log(data["score"]).astype(float)

        # Normalize scores between 0 and 1 using Min-Max scaling for each dimension
        for dimension_id in data["dimension_id"].unique():
            data.loc[data["dimension_id"] == dimension_id, "score"] = \
                MinMaxScaler(feature_range=(0, 1)).fit_transform(
                    data.loc[data["dimension_id"] == dimension_id, ["score"]]
                )

        # Add category_id
        data["category_id"] = 3

        # Add start_date and end_date
        data["start_date"] = datetime(2023, 1, 1).date()
        data["end_date"] = datetime(2099, 12, 31).date()

        # Add raw_value
        data["raw_value"] = None

        # Add ref_start_location_id
        data["ref_start_location_id"] = -1

        return data[["location_id", "category_id", "dimension_id", "start_date", "end_date", "ref_start_location_id", "score", "raw_value"]]

"""
# Connect to the database
db = Database()
db.connect()

data = CultureScores(db).get()

# Display the result
print(data[["location_id", "category_id", "dimension_id", "start_date", "end_date", "ref_start_location_id", "score", "raw_value"]].sort_values(by="score", ascending=False).head(50))

db.disconnect()
"""