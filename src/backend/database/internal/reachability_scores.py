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

        db.connect()
        land_reach = db.fetch_data("raw_reachability_land")
        db.disconnect()

        score_data = []

        for k, v in DIMENSION_IDS['land'].items():

            land_reach['location_id'] = land_reach['loc_id']
            land_reach['raw_value'] = land_reach[k].replace(0, np.nan)
            land_reach['score'] = MinMaxScaler(feature_range=(0, 1)).fit_transform(-land_reach[[k]])
            land_reach['dimension_id'], land_reach['category_id'] = v, CATEGORY_ID   
            land_reach["start_date"], land_reach["end_date"] = "2024-01-01", "2099-12-31"

            score_data.append(land_reach[["location_id", "category_id", "dimension_id", "start_date", "end_date", "score", "raw_value", "ref_id"]])

        return pd.concat(score_data)
    

    def get_air_reachability_scores(self):
        """
        Creates air reachability scores for all (location, start+end date, reference location) combinations
        """

        db = self.db

        db.connect()
        air_reach = db.fetch_data("raw_reachability_air")
        start_refs = db.fetch_data("core_ref_start_locations")
        core_locs = db.fetch_data("core_locations")
        db.disconnect()

        score_data = []

        for k, v in DIMENSION_IDS['air'].items():

            air_reach['start_date'] = air_reach['dep_date']
            air_reach['end_date'] = pd.to_datetime(air_reach['start_date']) + pd.Timedelta(days=7)
            air_reach['raw_value'] = air_reach[k].replace(0, np.nan)
            air_reach['score'] = MinMaxScaler(feature_range=(0, 1)).fit_transform(-air_reach[[k]])
            air_reach['dimension_id'], air_reach['category_id'] = v, CATEGORY_ID

            score_data.append(air_reach[["dest_iata", "category_id", "dimension_id", "start_date", 'end_date', "score", "raw_value", "orig_iata"]]) 

        score_data = pd.concat(score_data)

        # merge on start_refs to create combinations of destination airport, period, and start location
        start_refs['mapped_start_airport'] = start_refs['mapped_start_airport'].str.strip()
        score_data = score_data.merge(start_refs[['location_id', "mapped_start_airport"]], left_on="orig_iata", right_on="mapped_start_airport")
        score_data = score_data.rename(columns={"location_id": "ref_id"})

        # merge on core_locs to create combinations of destination, period, and start location
        score_data = score_data.merge(core_locs[['location_id', 'airport_1']], left_on="dest_iata", right_on="airport_1")

        return score_data[["location_id", "category_id", "dimension_id", "start_date", "end_date", "score", "raw_value", "ref_id"]]

        
    def concat_land_air_scores(self):
        ''' Get the reachability scores
        Input:  None
        Output: reachability scores
        '''
        # Get the data for the current and next year
        land = self.get_land_reachability_scores()
        air = self.get_air_reachability_scores()

        # Merge the data
        return pd.concat([land, air], axis=0)
    
    