# Add backend folder to sys.path
import os
import sys
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database
from database.internal.cost_scores import CostScores
from faker import Faker
import numpy as np
import pandas as pd

####----| SCRIPT FOR CREATING DUMMY DATA |----####
"""
db = Database()
db.connect()
cities = db.fetch_data(total_object='core_locations')
db.disconnect()

# Set up Faker for generating fake data
fake = Faker()

# Define the dimensions
dimensions = ['weather', 'safety', 'culture', 'costs', 'travel', 'health']

# Create a DataFrame with location_id, city, country, dimension, subcategory, scores
dummy_data = []

for _, row in cities.iterrows():
    location_id = row['location_id']
    city = row['city']
    country = row['country']

    for dimension in dimensions:
        subcategory = ""
        scores = np.random.uniform(0, 5)

        dummy_data.append({
            'location_id': location_id,
            'city': city,
            'country': country,
            'dimension': dimension,
            'subcategory': subcategory,
            'scores': scores
        })

df = pd.DataFrame(dummy_data)


db.connect()
db.insert_data(df, 'core_location_scores')
db.disconnect()
"""


####----| Assign scores to each location and fill in core_location_scores |----####

###----| Costs |----###

class FillScores:
    # Class for filling in the scores in the core_location_scores table
    def __init__(self, db:Database, locations:pd.DataFrame) -> None:
        ''' Initialize the class
        Input:  - db: Database object
                - locations: master data
        Output: None
        '''
        self.db = db
        self.locations = locations


    def cost_scores(self):
        ''' Fill in the cost scores
        Input:  - self.db: Database object
                - self.locations: master data
        Output: None
        '''        
        # Get the scores
        scores = CostScores(self.db).numbeo_scores()

        # Filter scores where location_id is not null and turn into int
        city_scores = scores[scores["location_id"].notnull()]
        city_scores["location_id"] = city_scores["location_id"].astype(int)
        # Filter scores where location_id is null
        country_scores = scores[scores["location_id"].isnull()]

        # Merge city scores
        city_data = self.locations.merge(city_scores[["location_id", "score"]], on=["location_id"], how='left')

        # Filter out cities that do not have a score
        no_scores = city_data[city_data["score"].isnull()]
        city_data = city_data[city_data["score"].notnull()]

        # Merge country scores
        country_data = no_scores.merge(country_scores[["country", "score"]], on=["country"], how='left')

        # If score_y is filled, use that, otherwise use score
        country_data["score"] = np.where(
            country_data["score_x"].isnull(),
            country_data["score_y"],
            country_data["score_x"]
        )

        # Combine the results of both merges
        location_scores = pd.concat([city_data, country_data])

        # Add dimension column and reorder
        location_scores["dimension"] = "costs"
        location_scores["subcategory"] = None
        location_scores = location_scores[["location_id", "city", "country", "dimension", "subcategory", "score"]]

        return location_scores
    

    def fill_scores(self, explicit:bool = False):
        ''' Fill in all scores
        Input:  - self.db: Database object
                - self.locations: master data
                - explicit: bool, whether to explicitly add scores to the database or not (and perhaps update existing scores)
        Output: None
        '''
        # Get the scores
        cost_scores = self.cost_scores()

        # Filter out rows where score is null
        cost_scores = cost_scores[cost_scores["score"].notnull()]

        # Check for all location_ids if there is a score in the database. If true, replace. If not, add
        for _, row in cost_scores.iterrows():
            location_id = row["location_id"]
            dimension = row["dimension"]
            subcategory = row["subcategory"]
            score = row["score"]

            # Check if there is a score for this location_id and dimension
            sql = f"SELECT * FROM core_location_scores WHERE location_id = {location_id} AND dimension = '{dimension}' AND subcategory = '{subcategory}'"
            if self.db.fetch_data(sql=sql)["location_id"] is None and not explicit:
                # Add score
                print(f"Adding {dimension} score for {row['city']}, {row['country']}...")
                sql = f"INSERT INTO core_location_scores (location_id, dimension, subcategory, score) VALUES ({location_id}, '{dimension}', '{subcategory}', {score})"
                self.db.execute_sql(sql, commit=True)
            else:
                # Update score
                print(f"Updating {dimension} score for {row['city']}, {row['country']}...")
                sql = f"UPDATE core_location_scores SET scores = {score} WHERE location_id = {location_id} AND dimension = '{dimension}' AND subcategory = '{subcategory}'"
                self.db.execute_sql(sql, commit=True)
    
db = Database()
db.connect()
locations = db.fetch_data(total_object='core_locations')
print(FillScores(db, locations).fill_scores())
db.disconnect()
