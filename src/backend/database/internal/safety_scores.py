import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database
from datetime import datetime
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


class SafetyScores:
    "Class for calculating safety scores"
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
        data = self.db.fetch_data(total_object="raw_safety_country")

        # Add start_date and end_date
        data["start_date"] = datetime(2023, 1, 1).date()
        data["end_date"] = datetime(2099, 12, 31).date()

        # Bring into long format
        data = data.melt(
            id_vars=["iso2", "country_name", "start_date", "end_date"],
            value_vars=["crime_rate", "ecological_threat", "peace_index", "personal_freedom",
                        "political_stability", "rule_of_law", "terrorism_index"],
            var_name="dimension_id",
            value_name="score"
            )

        # Get dimension_id for each column
        sql = """
            SELECT dimension_id, dimension_name
            FROM core_dimensions
            WHERE category_id = 1
            """
        dimension_map = self.db.fetch_data(sql=sql)
        dimension_map = {row["dimension"]: row["dimension_id"] for _, row in dimension_map.iterrows()}
        data["dimension_id"] = data["dimension_id"] \
            .map(dimension_map)

        # Normalize scores between 0 and 1 using Min-Max scaling for each dimension
        for dimension_id in data["dimension_id"].unique():
            data.loc[data["dimension_id"] == dimension_id, "score"] = \
                MinMaxScaler(feature_range=(0, 1)).fit_transform(
                    data.loc[data["dimension_id"] == dimension_id, ["score"]]
                )

        # Add category_id
        data["category_id"] = self.db.fetch_data(sql="SELECT category_id FROM core_categories WHERE category_id = 1").iloc[0, 0]

        return data[["iso2", "country_name", "category_id", "dimension_id", "start_date", "end_date", "score"]]





# First idea of calculating safety scores
class OldSafetyScores:
    "Class for calculating safety scores"
    def __init__(self, db:Database) -> None:
        ''' Initialize the class
        Input:  db: Database object
        Output: None
        '''
        self.db = db


    def dbscan_scores(self, data: pd.DataFrame, by:str) -> pd.DataFrame:
        ''' Apply DBSCAN clustering to the features
        Input:  - self.db: Database object
                - data: DataFrame with safety data
                - by: city or country
        Output: DataFrame with cluster labels
        '''
        # Select relevant features
        if by == "city":
            features = data[["safety", "healthcare", "environmental_qual", "tolerance"]]
        elif by == "country":
            features = data[["political_stability", "rule_of_law", "personal_freedom", "crime_rate", "peace_index", "terrorism_index", "ecological_threat"]]

        # Standardize the features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)

        # Create DBSCAN model / load if exists
        current_script_directory = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_script_directory, f"../../../../res/models/safety_scores_{by}_dbscan.model")
        # Ensure that the directory structure exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            dbscan = load(path)
        else:
            dbscan = DBSCAN(eps=0.5, min_samples=5)

        # Apply DBSCAN clustering
        data["cluster"] = dbscan.fit_predict(scaled_features)

        # Calculate scores based on the inverse of the distance to cluster centroids
        cluster_distances = dbscan.transform(scaled_features)
        min_distances = cluster_distances.min(axis=0)
        data["score"] = 1 / (cluster_distances.min(axis=1) / min_distances.max())

        # Save model
        dump(dbscan, path)

        # Normalize scores between 0 and 5 using Min-Max scaling
        min_max_scaler = MinMaxScaler(feature_range=(0, 5))
        data["score"] = min_max_scaler.fit_transform(data[["score"]])

        # Add category id
        data["category_id"] = self.db.fetch_data(sql="SELECT category_id FROM core_categories WHERE category = 'safety'").iloc[0, 0]
        assert data["category_id"].notnull().all()

        # Add empty dimension id
        data["dimension_id"] = self.db.fetch_data(sql="SELECT dimension_id FROM core_dimensions WHERE dimension = 'safety'").iloc[0, 0]
        assert data["dimension_id"].notnull().all()

        return data


    def city_scores(self):
        ''' Calculate the safety scores based on the city data
        Input:  self.db: Database object
        Output: Scores for each city
        '''
        # Fetch the data
        data = self.db.fetch_data(total_object="raw_safety_city")

        # Apply DBSCAN clustering
        scores = self.dbscan_scores(data, "city")

        # Add location_id to each city
        cities = self.db.fetch_data(total_object="core_locations")
        scores = cities.merge(scores, on="city", how="left")

        # Drop cities without location_id
        scores = scores[scores["location_id"].notnull()]

        # Keep only relevant columns
        return scores[["location_id", "city", "country", "category_id", "dimension_id", "score"]]


    def country_scores(self):
        ''' Calculate the safety scores based on the country data
        Input:  self.db: Database object
        Output: Scores for each country
        '''
        # Fetch the data
        data = self.db.fetch_data(total_object="raw_safety_country")

        # Apply DBSCAN clustering
        scores = self.dbscan_scores(data, "country")

        # Add empty city column for later concactenation
        scores["city"] = None

        return scores[["location_id", "city", "country", "category_id", "dimension_id", "score"]]
    

    def get(self):
        "Get all scores"
        city_scores = self.city_scores()
        country_scores = self.country_scores()

        return pd.concat([city_scores, country_scores])