import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

class CostScores:
    "Class for calculating cost scores"
    def __init__(self, db:Database) -> None:
        ''' Initialize the class
        Input:  db: Database object
        Output: None
        '''
        self.db = db


    def numbeo_scores(self):
        ''' Calculate the cost scores based on the Numbeo data
        Input:  - self.db: Database object
                - num_clusters: number of clusters to use for K-means clustering
        Output: None
        '''
        # Fetch the data
        data = self.db.fetch_data(total_object="raw_costs_numbeo")

        # Select relevant features and trim data
        features = data.drop(["location_id", "city", "country", "updated_at"], axis=1)
        data = data[["location_id", "city", "country"]]

        # Dict to assign costs to correct group
        sql = """
            SELECT d.dimension_id, d.extras
            FROM
                core_dimensions d
                INNER JOIN core_categories c ON d.category_id = c.category_id
            WHERE
                c.category_name = 'cost'
                AND d.dimension_name not in ('travel_costs', 'accommodation_costs')
            """
        cost_map = self.db.fetch_data(sql=sql).to_dict()
        cost_map = {cost_map['dimension_id'][i]: eval(cost_map['extras'][i]) for i in range(len(cost_map['dimension_id']))}

        # Calculate scores for each location
        results = pd.DataFrame()
        for idx, row in data.iterrows():

            # Calculate scores for each dimension
            for dimension_id, columns in cost_map.items():
                # Select relevant features and initialize dimension results
                relevant_features = features.loc[idx, columns]
                loc_results = pd.DataFrame()
                loc_results["location_id"] = [row["location_id"]]
                loc_results["city"] = [row["city"]]
                loc_results["country"] = [row["country"]]

                # Calculate scores based on the sum of cost variables (cheaper has higher score)
                loc_results["score"] = -relevant_features.sum()

                # Add dimension_id
                loc_results["dimension_id"] = dimension_id

                # Add results to location results
                results = pd.concat([results, loc_results], axis=0)

            assert results["dimension_id"].notnull().all()

        # Normalize scores between 0 and 1 using Min-Max scaling for each dimension
        for dimension_id in results["dimension_id"].unique():
            results.loc[results["dimension_id"] == dimension_id, "score"] = \
                MinMaxScaler(feature_range=(0, 1)).fit_transform(
                    results.loc[results["dimension_id"] == dimension_id, ["score"]]
                )

        return results[["location_id", "city", "country", "dimension_id", "score"]]


    def get(self) -> pd.DataFrame:
        ''' Get all scores
        Input:  self: database and functions
        Output: None
        '''
        # Collect all scores
        data = self.numbeo_scores()

        # Add category_id
        category_id = self.db.fetch_data(sql="SELECT category_id FROM core_categories WHERE category_name = 'cost'").iloc[0, 0]
        data["category_id"] = category_id
        assert data["category_id"].notnull().all()

        return data

"""
# Connect to the database
db = Database()
db.connect()

data = CostScores(db).get()

# Display the result
print(data[["location_id", "city", "country", "category_id", "dimension_id", "score"]].sort_values(by="score", ascending=False).head(50))

db.disconnect()
"""