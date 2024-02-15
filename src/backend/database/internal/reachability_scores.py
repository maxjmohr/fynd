import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta


CATEGORY_ID = 6

DIMENSION_IDS = {
    'land':{
        "car_duration": 61,
        "pt_duration": 62
    },
    'air': {
        "avg_duration": 63
    }
}


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


class ReachabilityScores:
    "Class for calculating reachability scores"
    def __init__(self, db:Database) -> None:
        ''' Initialize the class
        Input:  db: Database object
        Output: None
        '''
        self.db = db


    def get_land_reachability_scores(self):
        """
        Creates land reachability scores for all (location, reference location) combinations from raw data using MinMaxScaler
        """

        db = self.db
        land_reach = db.fetch_data("raw_reachability_land")

        score_data = []

        for k, v in DIMENSION_IDS['land'].items():

            land_reach['location_id'] = land_reach['loc_id']
            land_reach['raw_value'] = land_reach[k].replace(0, np.nan)
            land_reach['raw_value'] = land_reach['raw_value'] / 60 # convert minutes to hours
            land_reach['dim_score'] = MinMaxScaler(feature_range=(0, 1)).fit_transform(-land_reach[[k]])
            land_reach['dimension_id'], land_reach['category_id'] = v, CATEGORY_ID   
            land_reach["start_date"], land_reach["end_date"] = "2024-01-01", "2099-12-31"
            land_reach.rename(columns={"ref_id": "ref_start_location_id"}, inplace=True)

            score_data.append(land_reach[["location_id", "category_id", "dimension_id", "start_date", "end_date", "dim_score", "raw_value", "ref_start_location_id"]])

        return pd.concat(score_data)


    def get_air_reachability_scores(self):
        """
        Creates air reachability scores for all (location, start+end date, reference location) combinations
        """

        db = self.db
        air_reach = db.fetch_data("raw_reachability_air")
        start_refs = db.fetch_data("core_ref_start_locations")
        core_locs = db.fetch_data("core_locations")

        score_data = []

        # create start and end date columns using map_dates function
        dates_map = map_dates(air_reach['dep_date'].unique())
        start_end = air_reach['dep_date'].apply(lambda x: dates_map[x])

        for k, v in DIMENSION_IDS['air'].items():

            air_reach[['start_date', 'end_date']] = pd.DataFrame(start_end.tolist(), index=air_reach.index)
            air_reach['raw_value'] = air_reach[k].replace(0, np.nan)
            air_reach['raw_value'] = air_reach['raw_value'] / 60 + 3 # convert minutes to hours and add 3 hours for airport time
            air_reach['dim_score'] = MinMaxScaler(feature_range=(0, 1)).fit_transform(-air_reach[[k]])
            air_reach['dimension_id'], air_reach['category_id'] = v, CATEGORY_ID

            score_data.append(air_reach[["dest_iata", "category_id", "dimension_id", "start_date", 'end_date', "dim_score", "raw_value", "orig_iata"]]) 

        score_data = pd.concat(score_data)

        # merge on start_refs to create combinations of destination airport, period, and start location
        start_refs['mapped_start_airport'] = start_refs['mapped_start_airport'].str.strip()
        score_data = score_data.merge(start_refs[['location_id', "mapped_start_airport"]], left_on="orig_iata", right_on="mapped_start_airport")
        score_data = score_data.rename(columns={"location_id": "ref_start_location_id"})

        # merge on core_locs to create combinations of destination, period, and start location
        score_data = score_data.merge(core_locs[['location_id', 'airport_1']], left_on="dest_iata", right_on="airport_1")

        return score_data[["location_id", "category_id", "dimension_id", "start_date", "end_date", "dim_score", "raw_value", "ref_start_location_id"]]

        
    def get(self):
        ''' 
        Get both land and air reachability scores, create global scores for them and concatenate them
        '''
        
        # Get the data for the current and next year
        land = self.get_land_reachability_scores()
        air = self.get_air_reachability_scores()

        full_reach = pd.concat([land, air], axis=0)
        full_reach['score'] = MinMaxScaler(feature_range=(0, 1)).fit_transform(-np.log(full_reach[['raw_value']]))

        return full_reach[['location_id', 'category_id', 'dimension_id', 'start_date', 'end_date', 'score', 'raw_value', 'ref_start_location_id']]