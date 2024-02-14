import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../"))
sys.path.append(parent_dir)

from database.db_helpers import Database

import ee
import json
import pandas as pd
import time


def get_land_coverage(location_id: str, geojson: dict, map: str) -> pd.DataFrame:
    """ Get segmentation stats of a geojson
    Input:  - location_id: id of the location
            - geojson: geojson of a city
            - map: name of the landcover map. Can either be "Copernicus" or "ESA"
    Output: land_coverage_shares: segmentation stats of the geojson
    """
    time.sleep(1)

    # Convert the geojson to an Earth Engine object
    if geojson["type"] == "Polygon":
        ee_object = ee.Geometry.Polygon(geojson["coordinates"])
    elif geojson["type"] == "MultiPolygon":
        ee_object = ee.Geometry.MultiPolygon(geojson["coordinates"])
    else:
        raise ValueError("Invalid geojson type. Type can either be 'Polygon' or 'MultiPolygon'.")


    # Get the landcover image
    if map == "Copernicus":
        landcover = ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019").select("discrete_classification")
        # Get class values and names
        class_values = [str(value) for value in landcover.getInfo()["properties"]["discrete_classification_class_values"]]
        class_names = landcover.getInfo()["properties"]["discrete_classification_class_names"]

    elif map == "ESA":
        landcover = ee.ImageCollection("ESA/WorldCover/v100").first()
        # Get class values and names
        class_values = [str(value) for value in landcover.getInfo()["properties"]["Map_class_values"]]
        class_names = landcover.getInfo()["properties"]["Map_class_names"]
    else:
        raise ValueError("Invalid map. Map can either be 'Copernicus' or 'ESA'.")
    # Zip class values and names
    classes = dict(zip(class_values, class_names))

    # Reduce the landcover image to the region of the geojson
    land_coverage = landcover.reduceRegion(reducer=ee.Reducer.frequencyHistogram(),
                                           geometry=ee_object,
                                           bestEffort=True
                                           ).getInfo()
    if map == "Copernicus":
        land_coverage = land_coverage["discrete_classification"]
    elif map == "ESA":
        land_coverage = land_coverage["Map"]


    # Convert the stats to a dataframe and replace class values with class names
    land_coverage = {value_class: value_land for key_land, value_land in land_coverage.items() for key_class, value_class in classes.items() if key_class == key_land}
    land_coverage = pd.DataFrame(land_coverage, index=[location_id]).rename_axis("location_id").reset_index()

    # Create a dataframe with the share of each class
    land_coverage_shares = land_coverage.copy()
    land_coverage_shares.iloc[:, 1:] = land_coverage_shares.iloc[:, 1:] \
        .div(land_coverage_shares.iloc[:, 1:] \
        .sum(axis=1), axis=0)

    rename_dict = {
        "Tree cover": "tree_cover",
        "Shrubland": "shrubland",
        "Grassland": "grassland",
        "Cropland": "cropland",
        "Built-up": "built_up",
        "Bare / sparse vegetation": "bare_sparse_vegetation",
        "Snow and ice": "snow_ice",
        "Permanent water bodies": "permanent_water",
        "Herbaceous wetland": "herbaceous_wetland",
        "Mangroves": "mangroves",
        "Moss and lichen": "moss_lichen"
    }

    # Check and add missing columns
    required_columns = list(rename_dict.keys())
    for column in required_columns:
        if column not in land_coverage_shares.columns:
            land_coverage_shares[column] = 0

    # Rename columns
    land_coverage_shares = land_coverage_shares.rename(columns=rename_dict)

    return land_coverage_shares[["location_id", "tree_cover", "shrubland", "grassland", "cropland", "built_up", "bare_sparse_vegetation", "snow_ice", "permanent_water", "herbaceous_wetland", "mangroves", "moss_lichen"]]

"""
db = Database()
db.connect()
loc = db.fetch_data(sql="SELECT * FROM core_locations")
loc = loc.iloc[0, :]
loc["geojson"] = json.loads(loc["geojson"])
db.disconnect()

if __name__ == "__main__":
    # Initialize Earth Engine
    ee.Initialize()
    # Get geographical data
    land_coverage, land_coverage_shares, landcover = get_land_coverage(loc["city"], loc["geojson"], "ESA")
    print(land_coverage_shares)
"""