import geemap
from geopy.geocoders import Nominatim
import ee
import json
import pandas as pd
import requests
from shapely.geometry import Point, mapping

def get_geojson(city: str, country: str, shape: str = "polygon", radius: int = 30) -> dict:
    """ Get geojson of a city
    Input:  - city: name of the city
            - country: name of the country
            - shape: shape of the geojson. Can either be "polygon" or "circle"
            - radius: radius of the circle in km. Only used if shape is "circle"
    Output: geojson: geojson of the city
    """
    if shape == "polygon":
        # Get geojson from nomatim API
        url = "http://nominatim.openstreetmap.org/search"
        params = {
            "city": city,
            "country": country,
            "polygon_geojson": 1,
            "format": "json"
        }
        response = requests.get(url, params=params)
        data = response.json()
        geojson = data[0]["geojson"]
        return geojson

    if shape == "circle":
        # Get location coordinates
        geolocator = Nominatim(user_agent="Max Mohr")
        coor = geolocator.geocode(city)
        # Create a point
        point = Point(coor.longitude, coor.latitude)
        # Create a circle around the point with a specific radius
        circle = point.buffer(radius)
        # Convert the circle to a GeoJSON object
        geojson = mapping(circle)
        return geojson

    else:
        raise ValueError("Invalid shape. Shape can either be 'polygon' or 'circle'.")

def get_land_coverage(map: str, params_geojson: dict) -> [pd.DataFrame, pd.DataFrame, ee.Image]:
    """ Get segmentation stats of a geojson
    Input:  - map: name of the landcover map. Can either be "Copernicus" or "ESA"
            - params_geojson: parameters to get geojson of a city
    Output: land_coverage: segmentation stats of the geojson
    """
    # Get geojson of a city
    geojson = get_geojson(city=params_geojson["city"],
                          country=params_geojson["country"],
                          shape=params_geojson["shape"],
                          radius=params_geojson["radius"]
                          )
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
    land_coverage = pd.DataFrame(land_coverage, index=[params_geojson["city"]]).rename_axis("city").reset_index()

    # Create a dataframe with the share of each class
    land_coverage_shares = land_coverage.copy()
    land_coverage_shares.iloc[:, 1:] = land_coverage_shares.iloc[:, 1:].div(land_coverage_shares.iloc[:, 1:].sum(axis=1), axis=0)

    return land_coverage, land_coverage_shares, landcover # perhaps for later display

params_geojson = {
    "city": "Tuebingen",
    "country": "Germany",
    "shape": "polygon",
    "radius": 5
}

if __name__ == "__main__":
    # Initialize Earth Engine
    ee.Initialize()
    # Get segmentation stats of the geojson
    land_coverage, land_coverage_shares, _ = get_land_coverage("ESA", params_geojson)
    print(land_coverage_shares)