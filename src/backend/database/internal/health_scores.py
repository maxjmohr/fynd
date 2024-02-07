import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database
from datetime import datetime
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


class HealthScores:
    "Class for calculating health scores"
    def __init__(self, db:Database) -> None:
        ''' Initialize the class
        Input:  db: Database object
        Output: None
        '''
        self.db = db


    def get(self) -> pd.DataFrame:
        ''' Calculate the safety scores on country level
        Input:  self.db: Database object
        Output: scores for each country
        '''
        # Fetch the data
        data = self.db.fetch_data(total_object="raw_health_numeric")

        # Add start_date and end_date
        data["start_date"] = datetime(2023, 1, 1).date()
        data["end_date"] = datetime(2099, 12, 31).date()

        # Add category_id and dimension_id
        sql = """
            SELECT category_id, dimension_id
            FROM core_dimensions
            WHERE category_id = 7
            """
        data["category_id"] = self.db.fetch_data(sql=sql).iloc[0, 0]
        data["dimension_id"] = self.db.fetch_data(sql=sql).iloc[0, 1]

        # Rename score column and normalize between 0 and 1 using Min-Max scaling
        data.rename(columns={"health_score": "score"}, inplace=True)
        data["score"] = MinMaxScaler(feature_range=(0, 1)).fit_transform(data[["score"]])

        # Add empty column for raw_value
        data["raw_value"] = None

        return data[["country_name", "category_id", "dimension_id", "start_date", "end_date", "score", "raw_value"]]

"""
# Connect to the database
db = Database()
db.connect()

data = HealthScores(db).get()

# Display the result
print(data[["country_name", "category_id", "dimension_id", "start_date", "end_date", "score"]].sort_values(by="score", ascending=False).head(50))

db.disconnect()
"""