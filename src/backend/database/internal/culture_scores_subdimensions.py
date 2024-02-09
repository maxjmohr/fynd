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

class CultureSubdimensionsScores:
    "Class to calculate the geography scores of a city on a more granular level (subdimensions)"
    def __init__(self, db:Database) -> None:
        ''' Initialize the class
        Input:  db: Database object
        Output: None
        '''
        self.db = db


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

        # Assign dimension id by 3000 + range of ascending place categories (301,302,...)
        data = data.assign(dimension_id=3000 + data.groupby("place_category").ngroup())

        # Drop duplicate places for the same location_id and dimension_id
        data = data.drop_duplicates(subset=["location_id", "dimension_id", "place_name"])

        # Per location_id and dimension_id, count distinct places
        data = data.groupby(["location_id", "dimension_id"])["dimension_id"] \
            .count() \
            .reset_index(name="score")

        # Convert score to log scale
        data["score"] = np.log(data["score"]).astype(float)

        # If a location_id and dimension_id combination is not present, add a dummy entry
        for location_id, dimension_id in zip(data["location_id"].unique(), data["dimension_id"].unique()):
            if dimension_id not in data[data["location_id"] == location_id]["dimension_id"].values:
                data = pd.concat([data, pd.DataFrame({"location_id": [location_id], "dimension_id": [dimension_id], "score": [0.]})])

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

        return data[["location_id", "category_id", "dimension_id", "start_date", "end_date", "score", "raw_value"]]

"""
# Connect to the database
db = Database()
db.connect()

data = CultureSubdimensionsScores(db).get()
# Save to csv
data.to_csv("culture_subdimensions_scores.csv", index=False)

# Display the result
print(data[["location_id", "category_id", "dimension_id", "start_date", "end_date", "score", "raw_value"]].sort_values(by="score", ascending=False).head(50))

db.disconnect()
"""

###=== Insert into database ===###
"""
# Connect to the database
db = Database()
db.connect()

data = CultureSubdimensionsScores(db).get()

# Insert into database
db.delete_data("raw_subscores_culture")
db.insert_data(data, "raw_subscores_culture")

db.disconnect()
"""