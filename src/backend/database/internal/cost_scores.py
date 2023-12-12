import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database

from joblib import dump, load
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler, StandardScaler

class CostScores:
    def __init__(self, db:Database) -> None:
        ''' Initialize the class
        Input:  - db: Database object
        Output: None
        '''
        self.db = db

    def numbeo_scores(self, num_clusters:int = 5):
        ''' Calculate the cost scores based on the Numbeo data
        Input:  - self.db: Database object
                - num_clusters: number of clusters to use for K-means clustering
        Output: None
        '''
        # Fetch the data
        data = self.db.fetch_data(total_object="raw_costs_numbeo")

        # Select relevant features
        features = data.drop(["location_id", "city", "country", "updated_at"], axis=1)

        # Standardize the features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)

        # Load model if it exists
        current_script_directory = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_script_directory, "../../../../res/models/costs_scores_numbeo_kmeans.model")
        # Ensure that the directory structure exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            kmeans = load(path)
        else:
            kmeans = KMeans(n_clusters=num_clusters, random_state=666)

        # Apply K-means clustering
        data["cluster"] = kmeans.fit_predict(scaled_features)

        # Calculate scores based on the inverse of the distance to cluster centroids
        cluster_distances = kmeans.transform(scaled_features)
        min_distances = cluster_distances.min(axis=0)
        data["score"] = 1 / (cluster_distances.min(axis=1) / min_distances.max()) # Inverse relationship

        # Normalize scores between 0 and 5 using Min-Max scaling
        min_max_scaler = MinMaxScaler(feature_range=(0, 5))
        data["score"] = min_max_scaler.fit_transform(data[["score"]])

        # Save model
        dump(kmeans, path)

        return data[["location_id", "city", "country", "score"]]

"""
# Connect to the database
db = Database()
db.connect()

data = CostScores(db).numbeo_scores()

# Display the result
print(data[["location_id", "city", "country", "score"]].sort_values(by="score", ascending=False).tail(50))

db.disconnect()"""