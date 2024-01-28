from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import numpy as np
from datetime import datetime, timedelta
import time
from tqdm import tqdm
import pandas as pd
import os
import sys
import requests
import json
from unidecode import unidecode
import argparse

# import database class from database module located in src/backend
sys.path.append("./src/backend")
from database.db_helpers import Database


def createAccomodationTable():
    """
    Creates the accomodation table in the database.
    """
    db = Database() 
    conn, cur, engine = db.connect()
    db.execute_sql("""
        CREATE TABLE IF NOT EXISTS raw_accommodation (
            location_id INTEGER NOT NULL,
            kayak_city VARCHAR(100) NOT NULL,
            kayak_country VARCHAR(50) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            n_hotels INTEGER,
            avg_price FLOAT,
            bin_height_1 INTEGER,
            bin_height_2 INTEGER,
            bin_height_3 INTEGER,
            bin_height_4 INTEGER,
            bin_height_5 INTEGER,
            bin_height_6 INTEGER,
            bin_height_7 INTEGER,
            bin_height_8 INTEGER,
            bin_height_9 INTEGER,
            bin_height_10 INTEGER,
            bin_height_11 INTEGER,
            bin_height_12 INTEGER,
            bin_height_13 INTEGER,
            bin_height_14 INTEGER,
            bin_height_15 INTEGER,
            bin_height_16 INTEGER,
            bin_height_17 INTEGER,
            bin_height_18 INTEGER,
            bin_height_19 INTEGER,
            bin_height_20 INTEGER,
            bin_height_21 INTEGER,
            bin_height_22 INTEGER,
            bin_height_23 INTEGER,
            bin_height_24 INTEGER,
            bin_height_25 INTEGER,
            bin_height_26 INTEGER,
            bin_height_27 INTEGER,
            bin_height_28 INTEGER,
            bin_height_29 INTEGER,
            bin_height_30 INTEGER,
            bin_bound_1 INTEGER,
            bin_bound_2 INTEGER,
            bin_bound_3 INTEGER,
            bin_bound_4 INTEGER,
            bin_bound_5 INTEGER,
            bin_bound_6 INTEGER,
            bin_bound_7 INTEGER,
            bin_bound_8 INTEGER,
            bin_bound_9 INTEGER,
            bin_bound_10 INTEGER,
            bin_bound_11 INTEGER,
            bin_bound_12 INTEGER,
            bin_bound_13 INTEGER,
            bin_bound_14 INTEGER,
            bin_bound_15 INTEGER,
            bin_bound_16 INTEGER,
            bin_bound_17 INTEGER,
            bin_bound_18 INTEGER,
            bin_bound_19 INTEGER,
            bin_bound_20 INTEGER,
            bin_bound_21 INTEGER,
            bin_bound_22 INTEGER,
            bin_bound_23 INTEGER,
            bin_bound_24 INTEGER,
            bin_bound_25 INTEGER,
            bin_bound_26 INTEGER,
            bin_bound_27 INTEGER,
            bin_bound_28 INTEGER,
            bin_bound_29 INTEGER,
            bin_bound_30 INTEGER,
            bin_bound_31 INTEGER, 
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01')
            );
                
        COMMENT ON TABLE raw_accommodation IS 'Table stores accomodation data for location, start_date, end_date triplets'
        """)
    
    db.disconnect()

    return None


def getAccomodationData(url, driver):
    """
    Gets the counts, interval bounds and the average price from a search request URL
    args:
        url: The URL of the search request
    returns:
        count: The number of hotels in the search request
        interval_bounds: The interval bounds of the price filter
        average_price: The average price of the hotels in the search request
    """

    driver.get(url)

    # Wait until the page is completely loaded (the progress bar is gone)
    try:
        time.sleep(2) # Wait a bit to make sure the progress bar is there
        max_wait = 40
        WebDriverWait(driver, max_wait).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.skp2-bar.skp2-zeroPct')))
    except:
        pass

    # handling of locations without any listings
    try:
        element = WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.XPATH, '//div[@class="yNPo-total"]'), "0 properties"))
        return ([0], None, None)

    except:
        pass

    def process_browser_log_entry(entry):
        response = json.loads(entry['message'])['message']
        return response

    browser_log = driver.get_log('performance') 
    events = [process_browser_log_entry(entry) for entry in browser_log]

    # Filter events
    events = [event for event in events if 'Network.response' in event['method']]
    poll_events = []
    for event in events:
        try:
            url = event['params']['response']['url']
            if 'poll' in url:
                poll_events.append(event)
        except:
            pass

    # Only keep the one with the latest timestamp
    poll_events.sort(key=lambda x: x['params']['timestamp'])

    # Get the response body
    try:
        event = poll_events[-1]
        response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': event["params"]["requestId"]})
        body = json.loads(response['body'])

    except:
        return False

    return (body['filterData']['price']['count'], body['filterData']['price']['values'], body['filterData']['price']['averagePrice']['price'])


def parseArguments():
    parser = argparse.ArgumentParser(description='Get accommodation data for a given location.')
    parser.add_argument('-s', '--start_date', type=str, help='The start date in the format YYYY-mm-dd.')
    parser.add_argument('-e', '--end_date', type=str, help='The end date in the format YYYY-mm-dd.')

    args = parser.parse_args()

    return args


def getLocationJSON(loc_name, country_name, mode):
    """
    Returns unique Kayak location identifier for a given location
    args:
        loc_name: The name of the location
    returns:
        The JSON response of the request
    """

    url = "https://www.kayak.com/mvm/smartyv2/search"

    querystring = {"f":"j",
                "s":"airportonly" if mode == "airport" else "50",
                "where":f"{loc_name}, {country_name}",
                "sv":"",
                "cv":"undefined",
                "c":"undefined",
                "searchId":"undefined",
                "v":"undefined"
                }

    payload = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Accept": "*/*",
        "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.kayak.de",
        "DNT": "1",
        "Sec-GPC": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Content-Length": "0",
        "TE": "trailers"
    }

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    if response.status_code != 200:
        print(f"{response.status_code} ({response.text})")
        return -1
    
    else:
        return response.json()

def parseLocationJSON(loc_name, country_name, mode):
    """
    Returns unique Kayak location identifier by parsing the json response

    """

    loc_json = getLocationJSON(loc_name, country_name, mode=mode)

    if loc_json == -1:
        return None
    
    elif len(loc_json) == 0:
        return None

    for res in loc_json:

        if res['loctype'] == "city":

            return {
                "city_id": None if "ctid" not in res else res['ctid'],
                "lat": None if "lat" not in res else res['lat'],
                "lon": None if "lng" not in res else res['lng'],
                "box_maxX": None if "box_maxX" not in res else res["box_maxX"],
                "box_maxY": None if "box_maxY" not in res else res["box_maxY"],
                "box_minX": None if "box_minX" not in res else res["box_minX"],
                "box_minY": None if "box_minY" not in res else res["box_minY"],
                "iata_code": None if "apicode" not in res else res["apicode"]
                        }
        
    return None

def createURLfromCityAndDate(city, country, dates, mode="accomodation", num_adults=2):
    """
    Creates a URL for a given city and date.
    Args:
        city (str): The city to search for.
        dates (list): A list of dates in the format YYYY-mm-dd.
    Returns:
        str: The URL for the given city and date.
    """

    # get the location id by issuing post request to Kayak, return none if location ID is not found

    loc_json = parseLocationJSON(city, country, mode=mode)

    if loc_json is None:
        return None
    
    city_id = loc_json['city_id']

    return f"https://www.kayak.com/hotels/{city},{country}-c{city_id}/{dates[0]}/{dates[1]}/{num_adults}adults?sort=rank_a"


def configureChromeDriver():
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    #options.add_argument("--headless")

    return caps, options


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


def getAccomodationData(url, driver):
    """
    Gets the counts, interval bounds and the average price from a search request URL
    args:
        url: The URL of the search request
    returns:
        count: The number of hotels in the search request
        interval_bounds: The interval bounds of the price filter
        average_price: The average price of the hotels in the search request
    """

    driver.get(url)

    # Wait until the page is completely loaded (the progress bar is gone)
    try:
        time.sleep(2) # Wait a bit to make sure the progress bar is there
        max_wait = 40
        WebDriverWait(driver, max_wait).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.skp2-bar.skp2-zeroPct')))
        
    except:
        pass

    try:
        n_props = int(driver.find_element(By.XPATH, '//div[@class="yNPo-total"]').text.replace(" properties", ""))
        if n_props == "0 properties":
            return 0

    except:
        pass

    def process_browser_log_entry(entry):
        response = json.loads(entry['message'])['message']
        return response

    logs = [process_browser_log_entry(entry) for entry in driver.get_log('performance') ]

    def log_filter_received(log_):
        return (
            log_.get('method') == 'Network.response'
            and "poll" in log_["params"]["response"]["url"]
        )
    
    last_rec = list(filter(log_filter_received, logs))
    last_rec.sort(key=lambda x: x['params']['timestamp'])

    if len(last_rec) == 0:
        print("No response received")
        return None
    
    last_rec = last_rec[-1]

    # Get the response body
    try:
        response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': last_rec["params"]["requestId"]})

        if response.status_code == 429:
            print(f"Too many requests, status code {response.status_code}")
            return 429

        body = json.loads(response['body'])

        body['n_props'] = n_props

        return body

    except:
        print("Could not get response body")
        return None
    

def getAccommodationData(url, driver):
    """
    Gets the counts, interval bounds and the average price from a search request URL
    args:
        url: The URL of the search request
    returns:
        count: The number of hotels in the search request
        interval_bounds: The interval bounds of the price filter
        average_price: The average price of the hotels in the search request
    """

    driver.get(url)

    # Wait until the page is completely loaded (the progress bar is gone)
    try:
        time.sleep(2) # Wait a bit to make sure the progress bar is there
        max_wait = 40
        WebDriverWait(driver, max_wait).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.skp2-bar.skp2-zeroPct')))
        
    except:
        pass

    try:
        n_props = int(driver.find_element(By.XPATH, '//div[@class="yNPo-total"]').text.replace(" properties", ""))
        if n_props == "0 properties":
            return 0

    except:
        pass

    def process_browser_log_entry(entry):
        response = json.loads(entry['message'])['message']
        return response

    browser_log = driver.get_log('performance') 
    events = [process_browser_log_entry(entry) for entry in browser_log]

    # Filter events
    events = [event for event in events if 'Network.response' in event['method']]
    poll_events = []
    for event in events:
        try:
            url = event['params']['response']['url']
            if 'poll' in url:
                poll_events.append(event)
        except:
            pass

    # Only keep the one with the latest timestamp
    poll_events.sort(key=lambda x: x['params']['timestamp'])

    try:
        last_rec = poll_events[-1]
        response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': last_rec["params"]["requestId"]})
        body = json.loads(response['body'])

        body['n_props'] = n_props

        return body

    except:
        print("Could not get response body")
        return None
    

def parseAccommodationData(json_body):
    
    acc_data = {}

    acc_data['n_hotels'] = json_body['totalCount']

    if acc_data['n_hotels'] == 0:
        acc_data['avg_price'] = 0

        for i in range(30):
            acc_data[f"bin_height_{i+1}"] = 0
            acc_data[f"bin_bound_{i+1}"] = 0

        acc_data['bin_bound_31'] = 0

        return acc_data

    acc_data['avg_price'] = json_body['filterData']['price']['averagePrice']['price']

    for i, v in enumerate(json_body['filterData']['price']['values']):

        acc_data[f"bin_bound_{i+1}"] = v

    for i, v in enumerate(json_body['filterData']['price']['count']):
        acc_data[f"bin_height_{i+1}"] = v

    return acc_data

def accommodationMain():

    # parse arguments to get start and end date
    args = parseArguments()
    if args.start_date is None or args.end_date is None:
        periods = [("2024-02-17", "2024-03-01")]
    else:
        periods = [(args.start_date, args.end_date)]

    #create_new = True

    periods = [("2024-02-17", "2024-03-01")]
    
    #if create_new: 
    createAccomodationTable()

    for cur_per in periods:

        counter, max_retries = 0, 5

        db = Database()
        db.connect()

        caps, options = configureChromeDriver()

        locations = db.fetch_data("core_locations")[['location_id', 'city', 'country']]
        accommodation_raw = db.fetch_data("raw_accommodation")

        # select rows from database that have start_date and end_date equal to the current period
        accommodation_raw = accommodation_raw[(pd.to_datetime(accommodation_raw['start_date']) == pd.to_datetime(cur_per[0])) 
                                              & (pd.to_datetime(accommodation_raw['end_date']) == pd.to_datetime(cur_per[1]))]

        ### -------- LOCATION FILTERING AND PREPROCESSING -------- ###

        bad_links = [
            "Chattogram, Bangladesh",
            "Jashore, Bangladesh",
            "Mymensingh, Bangladesh",
            "San Francisco Gotera, El Salvador",
            "Ar Rutbah, Iraq",
            "Fallujah, Iraq",
            "Al Salt, Jordan",
            "Mubarak Al-Kabeer, Kuwait",
            "Shahhat, Libya",
            "Tubruq, Libya"
        ]

        # also read in translations for locations with bad names
        if os.path.exists("./res/master_data/location_rename.json"):
            with open("./res/master_data/location_rename.json", "r", encoding="utf-8") as f:
                location_rename = json.load(f)

        # select only locations that have not been processed yet
        processed_locs = accommodation_raw['location_id'].values.tolist()

        locations = locations[~locations['location_id'].isin(processed_locs)]
        locations = locations[~locations['country'].isin(["Belarus", "Russia", "Iran"])] # Kayak does not show results for some countries due to government restrictions
        locations.loc[locations['country'] == "Czechia", 'country'] = "Czech Republic" # replace values of "Czechia" with "Czech Repulic"
        locations.loc[locations['city'] == "Hong Kong", "country"] = "Hong Kong" # set country for Hong Kong to Hong Kong
        locations['city'] = locations[['city', 'country']].apply(lambda x: location_rename[f"{x[0]}, {x[1]}"] if f"{x[0]}, {x[1]}" in location_rename.keys() else x[0],  axis=1)
        locations = locations[~locations['city'].isin(b.split(", ")[0] for b in bad_links)]    

        ### -------------------------------------------------- ###

        # loop through loc_id, city, country triplets
        for loc_id, city, country in tqdm(locations.values):

            print(f"Processing {city}, {country}...")

            url = createURLfromCityAndDate(city, country, cur_per)

            if url is None:
                print(f"Could not get URL for {city}, {country}")
                continue

            driver = webdriver.Chrome(desired_capabilities=caps, options=options)

            try: 
                json_body = getAccommodationData(url, driver)

            except:
                pass

            if json_body == 429:
                print("Too many requests, sleeping for 60 seconds")
                time.sleep(60)

            elif json_body == 0:
                continue

            elif json_body is None:
                print(f"Could not get data for {city}, {country}")
                continue

            elif json_body != 0 and json_body is not None:
                acc_data = parseAccommodationData(json_body)

                acc_data['location_id'] = loc_id
                acc_data['kayak_city'] = city
                acc_data['kayak_country'] = country
                acc_data['start_date'] = cur_per[0]
                acc_data['end_date'] = cur_per[1]
                acc_data['avg_price'] = acc_data['avg_price'] / (getDaysBetweenDates(cur_per[0], cur_per[1]) + 1)

                data = pd.DataFrame(acc_data, index=[0])
                db.insert_data(data, "raw_accommodation")

            driver.quit()        

        db.disconnect()

    return None

if __name__ == "__main__":
    accommodationMain()