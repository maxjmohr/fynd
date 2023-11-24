from geopy.geocoders import Nominatim
import ee
import os
import pandas as pd
import requests
from shapely.geometry import Point, mapping

def get_geojson(city: str, country: str, shape: str = "polygon", long: int = 0, lat: int = 0, radius: int = 30) -> [dict, list]:
    """ Get geojson of a city and its bounding box
    Input:  - city: name of the city
            - country: name of the country
            - shape: shape of the geojson. Can either be "polygon" or "circle"
            - radius: radius of the circle in km. Only used if shape is "circle"
    Output: - geojson: geojson of the city
            - bounding_box: bounding box of the city. Only returned if shape is "polygon"
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
        response = requests.get(url, params=params).json()
        geojson = response[0]["geojson"]
        bounding_box = response[0]["boundingbox"]
        return geojson, bounding_box

    if shape == "circle":
        # Create a point
        point = Point(long, lat)
        # Create a circle around the point with a specific radius
        circle = point.buffer(radius)
        # Convert the circle to a GeoJSON object
        geojson = mapping(circle)
        return geojson, None

    else:
        raise ValueError("Invalid shape. Shape can either be 'polygon' or 'circle'.")

def get_land_coverage(city: str, geojson: dict, map: str,) -> [pd.DataFrame, pd.DataFrame, ee.Image]:
    """ Get segmentation stats of a geojson
    Input:  - city: name of the city
            - geojson: geojson of a city
            - map: name of the landcover map. Can either be "Copernicus" or "ESA"
    Output: land_coverage: segmentation stats of the geojson
    """
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
    land_coverage = pd.DataFrame(land_coverage, index=[city]).rename_axis("city").reset_index()

    # Create a dataframe with the share of each class
    land_coverage_shares = land_coverage.copy()
    land_coverage_shares.iloc[:, 1:] = land_coverage_shares.iloc[:, 1:].div(land_coverage_shares.iloc[:, 1:].sum(axis=1), axis=0)

    return land_coverage, land_coverage_shares, landcover # perhaps for later display

def get_landmarks(starting_city: str, shape: str, bounding_box: list, long: int, lat: int, radius: int) -> pd.DataFrame:
    """ Get landmarks of a city and its region
    Input:  - city: name of the city
            - shape: area to search for landmarks. Can either be "box" or "circle"
            - bounding_box: bounding box of the city. Only used if shape is "box"
            - long: longitude of the city. Only used if shape is "circle"
            - lat: latitude of the city. Only used if shape is "circle"
            - radius: radius of the circle in km. Only used if shape is "circle"
    Output: landmarks: landmarks of the area
    """
    # Get the directory of the current script and read API key
    current_script_directory = os.path.dirname(os.path.abspath(__file__))
    path = "../../../res/api_keys/geoapify_apikey.txt"
    with open(os.path.join(current_script_directory, path), "r") as f:
        apikey = f.read()
    
    # Get landmarks from geoapify API
    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": "natural,national_park,beach",
        "conditions": "named", # only named places
        "limit": 200,
        "apiKey": apikey,
        "format": "json"
    }
    if shape == "box":
        params["filter"] = f"rect:{bounding_box[2]},{bounding_box[0]},{bounding_box[3]},{bounding_box[1]}"
    elif shape == "circle":
        params["filter"] = f"circle:{long},{lat},{radius}"
    else:
        raise ValueError("Invalid shape. Shape can either be 'box' or 'circle'.")
    response = requests.get(url, params=params).json()["features"]

    # Store the relevant columns in lists and convert to dataframe
    name, county, city, village, long, lat, categories = [[response[i]["properties"][prop] if prop in response[i]["properties"] else None for i in range(len(response))] for prop in ["name", "county", "city", "village", "lon", "lat", "categories"]]
    landmarks = pd.DataFrame({"starting_city": starting_city, "name": name, "county": county, "city": city, "village": village, "long": long, "lat": lat, "categories": categories})

    return landmarks

params = {
    # Parameters for get_geojson()
    "city": "Tuebingen",
    "country": "Germany",
    "shape_geojson": "polygon",
    "radius_geojson": 5,
    # Parameters for get_land_coverage()
    "map": "ESA", # and city
    # Parameters for get_landmarks()
    "shape_landmarks": "box",
    "radius_landmarks": 13000
}

def main(params: dict) -> [dict, pd.DataFrame, pd.DataFrame, ee.Image, pd.DataFrame]:
    """ Get all geographical data
    Input:  parameters (dict)
    Output: output of geographical data
    """
    # Get location coordinates
    geolocator = Nominatim(user_agent="Max Mohr")
    coor = geolocator.geocode(params["city"])
    # Get geojson of a city
    geojson, bounding_box = get_geojson(params["city"], params["country"], params["shape_geojson"], coor.longitude, coor.latitude, params["radius_geojson"])
    # Get segmentation stats of the geojson
    land_coverage, land_coverage_shares, landcover = get_land_coverage(params["city"], geojson, "ESA")
    # Get landmarks of the geojson
    landmarks = get_landmarks(params["city"], params["shape_landmarks"], bounding_box, coor.longitude, coor.latitude, params["radius_landmarks"])
    return geojson, land_coverage, land_coverage_shares, landcover, landmarks

if __name__ == "__main__":
    # Initialize Earth Engine
    ee.Initialize()
    # Get geographical data
    geojson, land_coverage, land_coverage_shares, landcover, landmarks = main(params)
    print(land_coverage_shares)
    print(landmarks)