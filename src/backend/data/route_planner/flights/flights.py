import requests
import json
import pandas as pd
import ssl

def generateAmadeusToken(path: str) -> str:
    """
    Generates an access token that can be used for the Amadeus API.
    Input: 
        path (string): path to the file containing the API key and secret
    Output:
        access token (string)
    """

    # Read API key and secret from file
    with open(path, "r") as f:
        api_key = f.readline().strip()
        api_secret = f.readline().strip()

    # Generate access token
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": "cAMyxeJeaX3yhM43tJbRX7apW61uZ3k0",
        "client_secret": "RbndqzURttG2HR8s"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(url, data=data, headers=headers)

    if response.status_code == 200:
        return response.json()['access_token']
    
    else:
        print(f"Error {response.status_code}: {response.text}")


def queryFlightPrice(token, orig, dest, n_adult, dep_date, n_child, n_infant, travel_class, nonstop, max_price) -> dict:
    """
    Queries the Amadeus API for flight prices.
    Input: 
        token (string): access token
        orig (string): origin airport code
        dest (string): destination airport code
        n_adult (int): number of adults
        dep_date (string): departure date (YYYY-MM-DD)
        n_child (int): number of children
        n_infant (int): number of infants
        travel_class (string): travel class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
        nonstop (string): whether the flight should be nonstop
        max_price (float): maximum price in EUR
    Output: 
        flight prices (dictionary)
    """

    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"

    params = {
        "originLocationCode": orig,
        "destinationLocationCode": dest,
        "adults": n_adult,
        "departureDate": dep_date,
        "children": n_child,
        "infants": n_infant,
        "travelClass": travel_class,
        "nonStop": nonstop,
        "maxPrice": max_price,
    }

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        return response.json()
    
    else:
        print(f"Error {response.status_code}: {response.text}")


def readInAirportCodes(path, fetch=True):
    """
    Reads in the airport codes either from the github repo or from the local file and returns a pandas dataframe.
    Input: path (string): path to the file containing the airport codes
    Output: airport_codes (pandas dataframe)
    """

    # Disable SSL certificate verification (not recommended for production)
    ssl._create_default_https_context = ssl._create_unverified_context

    if not fetch:
        airport_codes = pd.read_csv(path)

    else:
        airport_codes = pd.read_csv("https://github.com/lxndrblz/Airports/raw/main/airports.csv")
        airport_codes.to_csv(path, index=False)

    return airport_codes


def main():

    orig = "FRA"
    dest = "ROM"
    n_adult = 1
    dep_date = "2023-11-29"
    n_child = 0
    n_infant = 0
    travel_class = "ECONOMY"
    nonstop = "true"
    max_price = 1000

    # Read in airport codes
    airport_codes = readInAirportCodes("./airport_codes.csv")

    # Get access token
    token = generateAmadeusToken("./../../../../res/auth/amadeus_apikey.txt")

    # Query flight prices
    flight_prices = queryFlightPrice(token, orig, dest, n_adult, dep_date, n_child, n_infant, travel_class, nonstop, max_price)

    # Print flight prices
    print(json.dumps(flight_prices, indent=4, sort_keys=True))


if __name__ == "__main__":
    main()