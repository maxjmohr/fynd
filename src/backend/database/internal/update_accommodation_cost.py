import math
import numpy as np
import pandas as pd
from datetime import datetime

import os
import sys
sys.path.append("/Users/mAx/Documents/Master/03/Data_Science_Project/01_Repository/src/backend")

from database.db_helpers import Database


def getDaysBetweenDates(start_date, end_date):
    """
    Returns the number of days between two dates
    args:
        start_date: The start date
        end_date: The end date
    returns:
        The number of days between the two dates
    """
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    return (end_date - start_date).days

def calculate_median_average(row):

    bounds = [row[f"bin_bound_{i+1}"] for i in range(30)]
    heights = [row[f"bin_height_{i+1}"] for i in range(29)]

    # Check if the sizes of bounds and heights are compatible
    if len(bounds) != len(heights) + 1:
        raise ValueError("The size of bounds should be one more than the size of heights")

    if (sum(heights) == 0) or (sum(bounds) == 0):
        return None, None

    # Calculate the midpoints of the bins
    midpoints = [(bounds[i] + bounds[i+1]) / 2 for i in range(len(bounds) - 1)]

    # Calculate the total number of data points
    total_points = sum(heights)

    # Calculate the average
    average = sum(midpoints[i] * heights[i] for i in range(len(midpoints))) / total_points

    # Calculate the cumulative heights
    cumulative_heights = np.cumsum(heights)

    # Find the bin that contains the median
    median_bin_index = np.searchsorted(cumulative_heights, total_points / 2)

    # Calculate the median
    if total_points % 2 == 0:
        # If there's an even number of data points, the median is the average of the two middle points
        median = (bounds[median_bin_index] + bounds[median_bin_index + 1]) / 2
    else:
        # If there's an odd number of data points, the median is the middle point
        median = bounds[median_bin_index]

    total_booking_days = getDaysBetweenDates(row['start_date'].strftime("%Y-%m-%d"), row['end_date'].strftime("%Y-%m-%d")) + 1

    return median / total_booking_days, average / total_booking_days


db = Database()
db.connect()
raw_acc = db.fetch_data("raw_accommodation")
raw_acc[['comp_median', 'comp_avg']] = raw_acc.apply(lambda x: pd.Series(calculate_median_average(x)), axis=1)

for index, row in raw_acc.iterrows():

    # Get the values from the DataFrame row
    location_id = row['location_id']
    comp_median = row['comp_median']
    comp_avg = row['comp_avg']

    # Check for NaN values
    if math.isnan(comp_median):
        comp_median_sql = 'NULL'
    else:
        comp_median_sql = comp_median

    if math.isnan(comp_avg):
        comp_avg_sql = 'NULL'
    else:
        comp_avg_sql = comp_avg

    # Update the database
    query = f"""
            UPDATE raw_accommodation
            SET comp_median = {comp_median_sql},
                comp_avg = {comp_avg_sql}
            WHERE
                location_id = {location_id}
                AND start_date = '{row['start_date'].strftime("%Y-%m-%d")}'
            """

    # Execute the SQL query
    db.execute_sql(query)

db.disconnect()