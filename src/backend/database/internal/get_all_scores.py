# Add backend folder to sys.path
import os
import sys
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database
from database.internal.cost_scores import CostScores
from database.internal.safety_scores import SafetyScores
from database.internal.weather_scores import WeatherScores
from datetime import datetime
from faker import Faker
import numpy as np
import pandas as pd

####----| SCRIPT FOR CREATING DUMMY DATA |----####
"""
db = Database()
db.connect()
db.delete_data('core_scores')
cities = db.fetch_data(total_object='core_locations')
db.disconnect()

# Set up Faker for generating fake data
fake = Faker()

# Get categories and dimensions
cat_dim = db.fetch_data(total_object='core_dimensions')[['category_id', 'dimension_id']]

# Create a DataFrame with location_id, city, country, dimension, subcategory, scores
dummy_data = []

for _, row in cities.iterrows():
    location_id = row['location_id']
    city = row['city']
    country = row['country']

    for _, row in cat_dim.iterrows():
        category_id = row['category_id']
        dimension_id = row['dimension_id']
        score = np.random.uniform(0, 1)

        dummy_data.append({
            'location_id': location_id,
            'category_id': category_id,
            'dimension_id': dimension_id,
            'score': score
        })

df = pd.DataFrame(dummy_data)


db.connect()
db.insert_data(df, 'core_scores')
db.disconnect()
"""


####----| Assign scores to each location and fill in core_scores |----####

class FillScores:
    "Class for filling in the scores in the core_scores table"
    def __init__(self, db:Database) -> None:
        ''' Initialize the class
        Input:  db: Database object
        Output: None
        '''
        self.db = db
        self.locations = db.fetch_data(total_object='core_locations')


###----| Costs |----###

    def cost_scores(self) -> pd.DataFrame:
        ''' Fill in the cost scores
        Input:  - self.db: Database object
                - self.locations: master data
        Output: location scores
        '''        
        # Get the cost of living scores
        scores = CostScores(self.db).get()
        # Delete the currently saved cost of living scores
        for dimension_id in scores["dimension_id"].unique():
            sql = f"DELETE FROM core_scores WHERE dimension_id = '{dimension_id}'"
            self.db.execute_sql(sql, commit=True)

        #####---| City level scores |---#####
        # Filter scores where location_id is not null and turn into int
        city_scores = scores[scores["location_id"].notnull()]
        city_scores["location_id"] = city_scores["location_id"].astype(int)
        # Filter scores where location_id is null
        country_scores = scores[scores["location_id"].isnull()]

        # Merge city scores
        city_data = self.locations.merge(
            city_scores[["location_id", "category_id", "dimension_id", "score"]],
            on=["location_id"],
            how="left")


        ######---| Country level scores |---#####
        # Filter out locations that do not have a score
        no_scores = city_data[city_data["score"].isnull()]
        city_data = city_data[city_data["score"].notnull()]

        # Delete the columns in no_scores that were added in the merge
        no_scores = no_scores.drop(["category_id", "dimension_id", "score"], axis=1)

        # Merge country scores
        country_data = no_scores.merge(
            country_scores[["country", "category_id", "dimension_id", "score"]],
            on=["country"],
            how="left")

        # Filter out locations that do not have a score
        country_data = country_data[country_data["score"].notnull()]


        ######---| Combine the results |---#####
        # Combine the results of both merges
        location_scores = pd.concat([city_data, country_data])

        # Add start_date and end_date column
        location_scores["start_date"] = "2024-01-01"
        location_scores["end_date"] = "2099-12-31"

        # Reorder
        location_scores = location_scores[["location_id", "category_id", "dimension_id", "start_date", "end_date", "score"]]

        return location_scores


###----| Safety |----###

    def safety_scores(self) -> pd.DataFrame:
        ''' Fill in the safety scores
        Input:  - self.db: Database object
                - self.locations: master data
        Output: location scores
        '''
        # Get the safety scores
        scores = SafetyScores(self.db).get()

        # Make sure that country_code and iso2 are both strings and have no leading or trailing whitespaces
        self.locations["country_code"] = self.locations["country_code"].str.strip()
        scores["iso2"] = scores["iso2"].str.strip()

        # Assign each location by country_code to score
        location_scores = self.locations.merge(
            scores[["iso2", "category_id", "dimension_id", "start_date", "end_date", "score"]],
            left_on=["country_code"], right_on=["iso2"],
            how="inner")

        # Reorder
        location_scores = location_scores[["location_id", "category_id", "dimension_id", "start_date", "end_date", "score"]]

        return location_scores


###----| Weather |----###

    def weather_scores(self) -> pd.DataFrame:
        ''' Fill in the weather scores
        Input:  - self.db: Database object
                - self.locations: master data
        Output: location scores
        '''
        # Get the weather scores
        return WeatherScores(self.db).get()


    def fill_scores(self, which_scores:dict, explicitely_update:bool = False):
        ''' Fill in all scores
        Input:  - self.db: Database object
                - self.locations: master data
                - which_scores: dict, which scores to fill in
                - explicitely_update: bool, whether to explicitly add scores to the database or not (and perhaps update existing scores)
        Output: None
        '''
        # Get the scores
        scores = pd.DataFrame(columns=["location_id", "category_id", "dimension_id", "start_date", "end_date", "score"])
        for category, function in which_scores.items():
            # Execute the function
            print(f"Getting scores for category {category}...")
            results = function()
            if not results.empty:
                scores = pd.concat([scores, results], axis=0)

        # Filter out rows where category_id or score is null
        scores = scores[scores["category_id"].notnull()]
        scores = scores[scores["score"].notnull()]

        # Make sure that the columns are correct dtypes
        scores["location_id"] = scores["location_id"].astype(int)
        scores["category_id"] = scores["category_id"].astype(int)
        scores["dimension_id"] = scores["dimension_id"].astype(int)
        scores["start_date"] = pd.to_datetime(scores["start_date"], format='%Y-%m-%d')
        scores["end_date"] = pd.to_datetime(scores["end_date"], format='%Y-%m-%d')

        # Replace all current scores with new scores
        if explicitely_update:
            print("Explicitely updating scores...")
            # Delete the currently saved scores
            for dimension_id in scores["dimension_id"].unique():
                print(f"Deleting all scores for dimension_id {dimension_id}...")
                sql = f"""
                    DELETE
                    FROM core_scores
                    WHERE dimension_id = '{dimension_id}'
                    """
                self.db.execute_sql(sql, commit=True)

            # Insert the scores
            print("Inserting new scores...")
            self.db.insert_data(data=scores, table="core_scores")

        # Else: check for all location_ids if there is a score in the database. If true, replace. If not, add
        else:
            for _, row in scores.iterrows():
                location_id = row["location_id"]
                category_id = row["category_id"]
                dimension_id = row["dimension_id"]
                start_date = row["start_date"]
                end_date = row["end_date"]
                score = row["score"]

                # Check if there is a score for this location, dimension and subcategory
                sql = f"""
                    SELECT location_id
                    FROM core_scores
                    WHERE
                        location_id = {location_id}
                        AND category_id = '{category_id}'
                        AND dimension_id = '{dimension_id}'
                        AND start_date = '{start_date}'
                        AND end_date = '{end_date}'
                    """
                if self.db.fetch_data(sql=sql).empty:
                    # Add score
                    print(f"Adding category_id {category_id} (dimension_id {dimension_id}) score for location_id {location_id}...")
                    sql = sql = f"""
                        INSERT INTO core_scores (location_id, category_id, dimension_id, start_date, end_date, score)
                        VALUES ({location_id}, '{category_id}', '{dimension_id}', '{start_date}', '{end_date}', {score})
                        """
                    self.db.execute_sql(sql, commit=True)
                else:
                    # Update score
                    print(f"Updating category_id {category_id} (dimension_id {dimension_id}) score for location_id {location_id}...")
                    sql = f"""
                        UPDATE core_scores
                        SET score = {score}
                        WHERE
                            location_id = {location_id}
                            AND category_id = '{category_id}'
                            AND dimension_id = '{dimension_id}'
                            AND start_date = '{start_date}'
                            AND end_date = '{end_date}'
                        """
                    self.db.execute_sql(sql, commit=True)


db = Database()
db.connect()
which_scores = {
    #'cost': FillScores(db).cost_scores
    'safety': FillScores(db).safety_scores
    #'weather': FillScores(db).weather_scores
}
FillScores(db).fill_scores(which_scores, explicitely_update=True)
db.disconnect()
