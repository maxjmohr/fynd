# Add backend folder to sys.path
import os
import sys
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database
from database.internal.cost_scores import CostScores
from database.internal.culture_scores import CultureScores
from database.internal.geography_scores import GeographyScores
from database.internal.health_scores import HealthScores
from database.internal.safety_scores import SafetyScores
from database.internal.weather_scores import WeatherScores
from database.internal.reachability_scores import ReachabilityScores
from datetime import datetime
#from faker import Faker
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

    def accommodation_cost_scores(self) -> pd.DataFrame:
        ''' Fill in the accommodation cost scores
        Input:  - self.db: Database object
                - self.locations: master data
        Output: location scores
        '''
        # Get the scores
        return CostScores(self.db).get(dimension="accommodation")

    
    def travel_cost_scores(self) -> pd.DataFrame:
        ''' Fill in the travel cost scores
        Input:  - self.db: Database object
                - self.locations: master data
        Output: location scores
        '''
        # Get the scores
        return CostScores(self.db).get(dimension="travel_cost")


    def cost_of_living_scores(self) -> pd.DataFrame:
        ''' Fill in the cost of living scores
        Input:  - self.db: Database object
                - self.locations: master data
        Output: location scores
        '''        
        # Get the cost of living scores
        scores = CostScores(self.db).get(dimension="cost_of_living")
        # Delete the currently saved cost of living scores
        for dimension_id in scores["dimension_id"].unique():
            sql = f"DELETE FROM core_scores WHERE dimension_id = '{dimension_id}'"
            self.db.execute_sql(sql, commit=True)

        #####---| City level scores |---#####
        # Filter scores where location_id is not null and turn into int
        city_scores = scores[scores["location_id"].notnull()]
        city_scores.loc[:, "location_id"] = city_scores["location_id"].astype(int)
        # Filter scores where location_id is null
        country_scores = scores[scores["location_id"].isnull()]

        # Merge city scores
        city_data = self.locations.merge(
            city_scores[["location_id", "category_id", "dimension_id", "start_date", "end_date", "ref_start_location_id", "score", "raw_value"]],
            on=["location_id"],
            how="left")


        ######---| Country level scores |---#####
        # Filter out locations that do not have a score
        no_scores = city_data[city_data["score"].isnull()]
        city_data = city_data[city_data["score"].notnull()]

        # Delete the columns in no_scores that were added in the merge
        no_scores = no_scores.drop(["category_id", "dimension_id", "start_date", "end_date", "score", "raw_value"], axis=1)

        # Merge country scores
        country_data = no_scores.merge(
            country_scores[["country", "category_id", "dimension_id", "start_date", "end_date", "ref_start_location_id", "score", "raw_value"]],
            on=["country"],
            how="left")

        # Filter out locations that do not have a score
        country_data = country_data[country_data["score"].notnull()]

        ######---| Combine the results |---#####
        # Combine the results of both merges
        location_scores = pd.concat([city_data, country_data])

        # Reorder
        location_scores = location_scores[["location_id", "category_id", "dimension_id", "start_date", "end_date", "ref_start_location_id", "score", "raw_value"]]

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

        # Assign each location by country_code to score
        location_scores = self.locations.merge(
            scores[["iso2", "category_id", "dimension_id", "start_date", "end_date", "ref_start_location_id", "score", "raw_value"]],
            left_on=["country_code"], right_on=["iso2"],
            how="inner")

        # Reorder
        return location_scores[["location_id", "category_id", "dimension_id", "start_date", "end_date", "ref_start_location_id", "score", "raw_value"]]


###----| Culture |----###
    def culture_scores(self) -> pd.DataFrame:
        ''' Fill in the culture scores
        Input:  - self.db: Database object
                - self.locations: master data
        Output: location scores
        '''
        # Get the culture scores
        return CultureScores(self.db).get()


###----| Weather |----###

    def weather_scores(self) -> pd.DataFrame:
        ''' Fill in the weather scores
        Input:  - self.db: Database object
                - self.locations: master data
        Output: location scores
        '''
        # Get the weather scores
        return WeatherScores(self.db).get()


###----| Geography |----###

    def geography_coverage_scores(self) -> pd.DataFrame:
        ''' Fill in the geography coverage scores
        Input:  - self.db: Database object
                - self.locations: master data
        Output: location scores
        '''
        # Get the coverage scores
        return GeographyScores(self.db).get_coverage_scores()


###----| Health |----###

    def health_scores(self) -> pd.DataFrame:
        ''' Fill in the health scores
        Input:  - self.db: Database object
                - self.locations: master data
        Output: location scores
        '''
        # Get the weather scores
        scores = HealthScores(self.db).get()

        # Change country_name for certain countries to fit
        scores["country_name"] = scores["country_name"].replace({
            "Taiwan, China": "Taiwan",
            "Czech Republic": "Czechia",
            "Macedonia": "North Macedonia"
        })

        # Assign each location by country_code to score
        location_scores = self.locations.merge(
            scores[["country_name", "category_id", "dimension_id", "start_date", "end_date", "ref_start_location_id", "score", "raw_value"]],
            left_on=["country"], right_on=["country_name"],
            how="inner")

        # Reorder
        return location_scores[["location_id", "category_id", "dimension_id", "start_date", "end_date", "ref_start_location_id", "score", "raw_value"]]
    

###----| Reachability |----###
    
    def get_reachability_scores(self) -> pd.DataFrame:
        """
        Fill in the reachability scores
        """
        return ReachabilityScores(self.db).get()

    @staticmethod
    def compute_distances(scores:pd.DataFrame, retrospective_update:bool=False) -> pd.DataFrame:
        ''' Compute the distance to the bottom 10 and top 10 quantile and to the median for each score
        Input:  - scores: dataframe with scores
                - retrospective_update: bool, whether to update the core_scores table or not
        Output: dataframe with scores and distances
        '''
        if retrospective_update:
            # Fetch scores table
            db = Database()
            db.connect()
            scores = db.fetch_data("core_scores")
            db.disconnect()

        # Get all unique combinations of category, dimension, start and end dates to find all separate scores
        category_dimension_date_combs = scores[['category_id', 'dimension_id', 'start_date', 'end_date']].\
        value_counts(ascending=True).reset_index(name='count').drop('count', axis=1)

        df_list = []

        # Loop through all unique scores
        for i in range(len(category_dimension_date_combs)):

            # Create a filtered dataframe, consisting only of the location scores for one unique combination
            cat_dim_df = scores[(scores["category_id"]==category_dimension_date_combs.loc[i, "category_id"]) &
                                        (scores["dimension_id"]==category_dimension_date_combs.loc[i, "dimension_id"]) &
                                        (scores["start_date"]==category_dimension_date_combs.loc[i, "start_date"]) &
                                        (scores["end_date"]==category_dimension_date_combs.loc[i, "end_date"])].copy()

            # Compute relevant metrics
            median = cat_dim_df["score"].quantile(0.5)
            bottom_10 = cat_dim_df["score"].quantile(0.1)
            top_10 = cat_dim_df["score"].quantile(0.9)
            std = cat_dim_df["score"].std()

            # For each score in one dimension, check if it lays in the bottom 10 or top 10 quantile
            for idx, row in cat_dim_df.iterrows():
                if row["score"] < bottom_10:
                    # Compute distance like this to make sure that distance in bottom 10 are negative and top 10 are positive to be identifiable
                    cat_dim_df.loc[idx, "distance_to_bound"] = (row["score"] - bottom_10) / std
                elif row["score"] > top_10:
                    cat_dim_df.loc[idx, "distance_to_bound"] = (row["score"] - top_10) / std
                else:
                    # If score is inside the bounds, assign a "None" value to distance_to_bound
                    cat_dim_df.loc[idx, "distance_to_bound"] = None

                # Compute distance_to_median for all
                cat_dim_df.loc[idx, "distance_to_median"] = (row["score"] - median) / std

            # Add filtered dataframe with quantiles to list
            df_list.append(cat_dim_df)

        # Concat all combinations to reassemble the core_score table, now with computed distances
        return pd.concat(df_list).reset_index(drop=True)


    def fill_scores(self, which_scores:dict, explicitely_update:bool = False):
        ''' Fill in all scores
        Input:  - self.db: Database object
                - self.locations: master data
                - which_scores: dict, which scores to fill in
                - explicitely_update: bool, whether to explicitly add scores to the database or not (and perhaps update existing scores)
        Output: None
        '''
        # Get the scores
        scores = pd.DataFrame(columns=["location_id", "category_id", "dimension_id", "start_date", "end_date", "ref_start_location_id", "score", "raw_value", "distance_to_median", "distance_to_bound"])
        for category, function in which_scores.items():
            # Execute the function
            print(f"Getting scores for category {category}...")
            results = function()
            if not results.empty:
                scores = pd.concat([scores, results], axis=0)

        # Compute distances
        scores = self.compute_distances(scores, retrospective_update=False)

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
            self.db.insert_data(data=scores, table="core_scores", updated_at=True)

        # Else: check for all location_ids if there is a score in the database. If true, replace. If not, add
        else:
            for _, row in scores.iterrows():
                location_id = row["location_id"]
                category_id = row["category_id"]
                dimension_id = row["dimension_id"]
                start_date = row["start_date"]
                end_date = row["end_date"]
                ref_start_location_id = row["ref_start_location_id"]
                score = row["score"]
                raw_value = row["raw_value"]
                distance_to_bound = row["distance_to_bound"]
                distance_to_median = row["distance_to_median"]
                if raw_value is None:
                    raw_value = "NULL"

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
                        AND ref_start_location_id = '{ref_start_location_id}'
                    """
                if self.db.fetch_data(sql=sql).empty:
                    # Add score
                    print(f"Adding category_id {category_id} (dimension_id {dimension_id}) score for location_id {location_id}...")
                    sql = sql = f"""
                        INSERT INTO core_scores (location_id, category_id, dimension_id, start_date, end_date, ref_start_location_id, score, raw_value, distance_to_bound, distance_to_median)
                        VALUES ({location_id}, '{category_id}', '{dimension_id}', '{start_date}', '{ref_start_location_id}', '{end_date}', {score}, {raw_value}, {distance_to_bound}, {distance_to_median})
                        """
                    self.db.execute_sql(sql, commit=True)
                else:
                    # Update score
                    print(f"Updating category_id {category_id} (dimension_id {dimension_id}) score for location_id {location_id}...")
                    sql = f"""
                        UPDATE core_scores
                        SET score = {score}, raw_value = {raw_value}, distance_to_bound = {distance_to_bound}, distance_to_median = {distance_to_median}
                        WHERE
                            location_id = {location_id}
                            AND category_id = '{category_id}'
                            AND dimension_id = '{dimension_id}'
                            AND start_date = '{start_date}'
                            AND end_date = '{end_date}'
                            AND ref_start_location_id = '{ref_start_location_id}'
                        """
                    self.db.execute_sql(sql, commit=True)


db = Database()
db.connect()
which_scores = {
    #'accommodation_cost': FillScores(db).accommodation_cost_scores,
    #'travel_cost': FillScores(db).travel_cost_scores,
    #'cost_of_living': FillScores(db).cost_of_living_scores
    #'safety': FillScores(db).safety_scores
    #'culture': FillScores(db).culture_scores,
    #'weather': FillScores(db).weather_scores,
    #'geography_coverage': FillScores(db).geography_coverage_scores,
    #'health': FillScores(db).health_scores,
    #'reachability': FillScores(db).get_reachability_scores,
}
FillScores(db).fill_scores(which_scores, explicitely_update=True)
db.disconnect()
