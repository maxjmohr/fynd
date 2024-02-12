import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# helper function to create non-overlapping start and end dates
def map_dates(dates):

    dates.sort()

    # Convert dates to datetime
    dates = pd.to_datetime(dates)
    
    # Calculate midpoints
    midpoints = dates[:-1] + (dates[1:] - dates[:-1]) / 2
    
    # Initialize start date as today
    start_date = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))
    
    # Initialize dictionary
    date_dict = {}
    
    # Iterate over midpoints
    for i in range(len(midpoints)):
        # Calculate end date as day before next start date
        end_date = midpoints[i] - pd.Timedelta(days=1)
        
        # Add to dictionary
        date_dict[dates[i].strftime('%Y-%m-%d')] = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
        
        # Update start date
        start_date = midpoints[i]
    
    # Add last date
    end_date = dates[-1] + (dates[-1] - midpoints[-1])
    date_dict[dates[-1].strftime('%Y-%m-%d')] = (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    
    return date_dict


class CostScores:
    "Class for calculating cost scores"
    def __init__(self, db:Database) -> None:
        ''' Initialize the class
        Input:  db: Database object
        Output: None
        '''
        self.db = db


    def accommodation_scores(self) -> pd.DataFrame:
        ''' Calculate the accommodation scores based on the Numbeo data
        Input:  self.db: Database object
        Output: None
        '''
        # Fetch the data
        data = self.db.fetch_data(total_object="raw_accommodation")

        # Get dimension_id for accommodation
        data["dimension_id"] = 42

        # Convert USD to EUR (04.02.2024)
        data["comp_median"] = data["comp_median"] * 0.93

        # Add raw_value
        data["raw_value"] = data["comp_median"]

        # Convert comp_median to log scale
        data["comp_median"] = np.log(data["comp_median"])

        # Normalize scores between 0 and 1 using Min-Max scaling
        data["score"] = MinMaxScaler(feature_range=(0, 1)).fit_transform(-data[["comp_median"]])

        """for start_date in data["start_date"].unique():
            data.loc[data["start_date"] == start_date, "score"] = \
                MinMaxScaler(feature_range=(0, 1)).fit_transform(
                    data.loc[data["start_date"] == start_date, ["comp_median"]]
                )"""

        return data[["location_id", "dimension_id", "start_date", "end_date", "score", "raw_value"]]
    

    def travel_cost_scores(self) -> pd.DataFrame:
        """
        Creates travel cost scores for all (location, reference location, period) combinations from raw data using MinMaxScaler
        """
        
        db = self.db

        data = db.fetch_data("raw_reachability_air")
        start_refs = db.fetch_data(total_object = "core_ref_start_locations")
        core_locs = db.fetch_data(total_object = "core_locations")

        # create start and end date columns using map_dates function
        dates_map = map_dates(data['dep_date'].unique())
        start_end = data['dep_date'].apply(lambda x: dates_map[x])
        data[['start_date', 'end_date']] = pd.DataFrame(start_end.tolist(), index=data.index)

        # Get dimension_id for accommodation
        data["dimension_id"] = 41
        data['raw_value'] = data['avg_price'].replace(0, np.nan)
        data["score"] = MinMaxScaler(feature_range=(0, 1)).fit_transform(-np.log(data[["avg_price"]]))

        start_refs['mapped_start_airport'] = start_refs['mapped_start_airport'].str.strip()
        data = data.merge(start_refs[['location_id', "mapped_start_airport"]], left_on="orig_iata", right_on="mapped_start_airport")
        data = data.rename(columns={"location_id": "ref_start_location_id"})

        # merge on core_locs to create combinations of destination, period, and start location
        score_data = data.merge(core_locs[['location_id', 'airport_1']], left_on="dest_iata", right_on="airport_1")

        return score_data[["location_id", "dimension_id", "start_date", "end_date", "score", "raw_value", "ref_start_location_id"]]


    def numbeo_scores(self):
        ''' Calculate the cost scores based on the Numbeo data
        Input:  self.db: Database object
        Output: None
        '''
        # Fetch the data
        data = self.db.fetch_data(total_object="raw_costs_numbeo")

        # Select relevant features and trim data
        features = data.drop(["location_id", "city", "country", "updated_at"], axis=1)
        data = data[["location_id", "city", "country"]]

        # Dict to assign costs to correct group
        sql = """
            SELECT dimension_id, extras
            FROM core_dimensions
            WHERE
                category_id = 4
                AND dimension_name not in ('Travel', 'Accommodation')
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
                loc_results["score"] = relevant_features.sum()
                loc_results["raw_value"] = loc_results["score"]

                # Add dimension_id
                loc_results["dimension_id"] = dimension_id

                # Add results to location results
                results = pd.concat([results, loc_results], axis=0)

            assert results["dimension_id"].notnull().all()

        # Convert score to log scale
        results["score"] = np.log(results["score"])

        # Normalize scores between 0 and 1 using Min-Max scaling for each dimension
        for dimension_id in results["dimension_id"].unique():
            results.loc[results["dimension_id"] == dimension_id, "score"] = \
                MinMaxScaler(feature_range=(0, 1)).fit_transform(
                    -results.loc[results["dimension_id"] == dimension_id, ["score"]]  # Lower costs result in higher score
                )

        # Add start_date and end_date column
        results["start_date"] = "2024-01-01"
        results["end_date"] = "2099-12-31"

        return results[["location_id", "city", "country", "dimension_id", "start_date", "end_date", "score", "raw_value"]]


    def get(self, dimension:str) -> pd.DataFrame:
        ''' Get all scores
        Input:  - self: database and functions
                - dimension: which dimension scores to get
        Output: None
        '''
        # Collect the scores
        if dimension == "accommodation":
            data = self.accommodation_scores()
        elif dimension == "cost_of_living":
            data = self.numbeo_scores()
        elif dimension == "travel_cost":
            data = self.travel_cost_scores()

        # Add category_id
        data["category_id"] = 4
        assert data["category_id"].notnull().all()

        return data

"""
# Connect to the database
db = Database()
db.connect()

data = CostScores(db).get(dimension="accommodation")
#data = CostScores(db).get(dimension="cost_of_living")

# Save data to csv
data.to_csv("cost_scores_median_log.csv", index=False)

# Display the result
print(data[["location_id", "category_id", "dimension_id", "start_date", "end_date", "score", "raw_value"]].sort_values(by="score", ascending=False).head(50))

db.disconnect()
"""