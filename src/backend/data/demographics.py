import requests
from geopy.geocoders import Nominatim
import pandas as pd

# Get location coordinates
location = "Tuebingen"
geolocator = Nominatim(user_agent="Max Mohr")
coor = geolocator.geocode(location)

url = "https://api.worldpop.org/v1/wopr/pointagesex"
params = {
    "iso3": "NGA",
    "ver": "1.2",
    "lat": coor.latitude,
    "lon": coor.longitude,
    "agesex": ["m0", "m1", "m5", "m10", "m15", "m20", "m25", "m30", "m35", "m40", "m45", "m50", "m55", "m60", "m65", "m70", "m75", "m80",
               "f0", "f1", "f5", "f10", "f15", "f20", "f25", "f30", "f35", "f40", "f45", "f50", "f55", "f60", "f65", "f70", "f75", "f80"]
}
response = requests.get(url, params=params)
print(response.json())

def get_pop_total(location: str) -> pd.DataFrame:
    """
    Input: location (string)
    Output: total population data (pandas dataframe)
    """
    # Get location population (total)
    url = "https://documentation-resources.opendatasoft.com/api/explore/v2.1/catalog/datasets/geonames-all-cities-with-a-population-1000/records?limit=1&refine=alternate_names%3A" + location
    response = requests.get(url).json()

    # Store variables in dicitionary and return it as a dataframe
    out = {}
    out["location"] = location
    out["population"] = response['results'][0]['population']
    out["modification_date"] = response['results'][0]['modification_date']

    return pd.DataFrame(data = out, index=[0])

print(get_pop_total("Tuebingen"))