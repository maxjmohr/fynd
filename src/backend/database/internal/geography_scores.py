import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database
from datetime import datetime
import pandas as pd


class GeographyScores:
    "Class to calculate the geography scores of a city"
    def __init__(self, db:Database) -> None:
        ''' Initialize the class
        Input:  db: Database object
        Output: None
        '''
        self.db = db


    def get_coverage_scores(self) -> pd.DataFrame:
        ''' Get the coverage scores of a city
        Input:  db
        Output: coverage_scores: coverage scores of a city
        '''
        # Fetch the data
        data = self.db.fetch_data(total_object="raw_geography_coverage")

        # Bring into long format
        data = data.melt(
            id_vars=["location_id"],
            value_vars=["tree_cover", "shrubland", "grassland", "cropland", "built_up", "bare_sparse_vegetation",
                        "snow_ice", "permanent_water", "herbaceous_wetland", "mangroves", "moss_lichen"],
            var_name="dimension_id",
            value_name="score"
            )

        # Map the dimension_id
        sql = """
            SELECT dimension_id, dimension_name
            FROM core_dimensions
            WHERE category_id = 5
            """
        dimension_map = self.db.fetch_data(sql=sql)
        dimension_map = {row["dimension"]: row["dimension_id"] for _, row in dimension_map.iterrows()}
        data["dimension_id"] = data["dimension_id"] \
            .map(dimension_map)

        # Add category_id
        data["category_id"] = self.db.fetch_data(sql="SELECT category_id FROM core_categories WHERE category_id = 5").iloc[0, 0]

        # Add start_date and end_date
        data["start_date"] = datetime(2023, 1, 1).date()
        data["end_date"] = datetime(2099, 12, 31).date()

        # Add raw_value_formatted
        data["raw_value_formatted"] = None

        return data[["location_id", "category_id", "dimension_id", "start_date", "end_date", "score", "raw_value_formatted"]]

"""
# Connect to the database
db = Database()
db.connect()

data = GeographyScores(db).get_coverage_scores()

# Display the result
print(data[["location_id", "category_id", "dimension_id", "start_date", "end_date", "score"]].sort_values(by="score", ascending=False).head(50))

db.disconnect()
"""