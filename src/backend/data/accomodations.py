from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from datetime import datetime, timedelta
import numpy as np
import time
from tqdm import tqdm
import pandas as pd
import os
import sys
import requests
import json
from unidecode import unidecode
import argparse
import logging

from multiprocessing import Pool

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


def calculate_median_average(bounds, heights):
    # Check if the sizes of bounds and heights are compatible
    if len(bounds) != len(heights) + 1:
        raise ValueError("The size of bounds should be one more than the size of heights")

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

    return median, average

def generate_periods(start_date, end_date, duration):
    start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
    start_dates = pd.date_range(start_date, end_date, freq=f'{duration}D')

    periods = []
    for i, start in enumerate(start_dates):
        end = start + timedelta(days=duration-1)
        if end > end_date:
            end = end_date
        periods.append((start, end))

    return periods


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


def configureChromeDriver(headless=False):
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    if headless: options.add_argument("--headless")

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

        # Check for the presence of the security check element
    try:
        driver.find_element(By.CSS_SELECTOR, '.WZTU-wrap')
        return -1
    
    except NoSuchElementException:
        pass

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
            if url == "https://www.kayak.com/i/api/search/dynamic/hotels/poll":
                request_url = url
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
        logging.warning(f"Could not get response body for {request_url}")
        print(f"Could not get response body for {request_url}")
        return None
    

def parseAccommodationData(json_body):
    
    try: 
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
    
    except:
        return None


def process_period(period):

    # convert periods to string
    period = [period[0].strftime("%Y-%m-%d"), period[1].strftime("%Y-%m-%d")]

    max_retries, sleep_timer = 80, 180
    cur_country, driver = None, None
    caps, options = configureChromeDriver()

    db = Database()
    db.connect()

    locations = db.fetch_data("core_locations")[['location_id', 'city', 'country']]
    accommodation_raw = db.fetch_data("raw_accommodation")

    db.disconnect()

    # select rows from database that have start_date and end_date equal to the current period
    accommodation_raw = accommodation_raw[(pd.to_datetime(accommodation_raw['start_date']) == pd.to_datetime(period[0])) 
                                          & (pd.to_datetime(accommodation_raw['end_date']) == pd.to_datetime(period[1]))]

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
        "Tubruq, Libya",
        "Dukhan, Qatar"
    ]

    # also read in translations for locations with bad names
    if os.path.exists("./res/master_data/location_rename.json"):
        with open("./res/master_data/location_rename.json", "r", encoding="utf-8") as f:
            location_rename = json.load(f)

    # select only locations that have not been processed yet
    processed_locs = accommodation_raw['location_id'].values.tolist()

    locations = locations[~locations['location_id'].isin(processed_locs)]

    if len(locations) == 0:
        logging.info(f"All locations have been processed for period {period}")
        print(f"All locations have been processed for period {period}")
        return None

    locations = locations[~locations['country'].isin(["Belarus", "Russia", "Iran"])] # Kayak does not show results for some countries due to government restrictions
    locations.loc[locations['country'] == "Czechia", 'country'] = "Czech Republic" # replace values of "Czechia" with "Czech Repulic"
    locations.loc[locations['location_id'] == 206579565, 'city'] = "Hong Kong"
    locations.loc[locations['location_id'] == 206579565, 'country'] = "Hong Kong"    
    locations['city'] = locations[['city', 'country']].apply(lambda x: location_rename[f"{x['city']}, {x['country']}"] if f"{x['city']}, {x['country']}" in location_rename.keys() else x['city'],  axis=1)
    locations = locations[~locations['city'].isin(b.split(", ")[0] for b in bad_links)] 
    locations = locations.sort_values(by='country', ascending=False) # from Z to A

    # batched processing of locations
    if len(locations) >= 200:
        locations = locations[:200]

    ### -------------------------------------------------- ###
        
    # loop through loc_id, city, country triplets
    for loc_id, city, country in tqdm(locations.values):

        counter = 0

        if cur_country != country:
            if driver:
                driver.quit()
            cur_country = country
            driver = webdriver.Chrome(desired_capabilities=caps, options=options)

        print(f"Processing {city}, {country} for period {period}...")

        url = createURLfromCityAndDate(city, country, period)

        if url is None:
            print(f"Could not get URL for {city}, {country}")
            continue

        try: 
            json_body = getAccommodationData(url, driver)

        except:
            pass

        if json_body == 429:
            print("Too many requests, sleeping for 180 seconds")
            counter += 1

            if counter >= max_retries:
                if driver:
                    driver.quit()
                time.sleep(sleep_timer)
                break

        elif json_body == 0:
            continue

        elif json_body == -1:
            print(f"Security check detected for {city}, {country}. Returning and sleeping for 180 seconds")
            if driver:
                driver.quit()
            time.sleep(sleep_timer)
            break

        elif json_body is None:
            print(f"Could not get data for {city}, {country}")
            counter += 1

            if counter >= max_retries:
                print("Maximum number of retries reached, skipping...")
                break
            
            continue

        else:

            try:
                acc_data = parseAccommodationData(json_body)

                bin_heights = [acc_data[k] for k in acc_data.keys() if "bin_height" in k]
                bin_bounds = [acc_data[k] for k in acc_data.keys() if "bin_bound" in k]

                appr_mean, appr_median = calculate_median_average(bin_bounds, bin_heights)
                total_booking_days = (getDaysBetweenDates(period[0], period[1]) + 1)

                acc_data['location_id'] = loc_id
                acc_data['kayak_city'], acc_data['kayak_country'] = city, country
                acc_data['start_date'], acc_data['end_date'] = period[0], period[1]
                acc_data['avg_price'] = acc_data['avg_price'] / total_booking_days
                acc_data['appr_mean'], acc_data['appr_median'] = appr_mean/total_booking_days, appr_median/total_booking_days
                db.connect()
                db.insert_data(pd.DataFrame(acc_data, index=[0]), "raw_accommodation")
                db.disconnect()

            except:
                print(f"Could not parse data for {city}, {country}")
                counter += 1

                if counter >= max_retries:
                    print("Maximum number of retries reached, skipping...")
                    break

        driver.quit()        

    return None


def accomodations_main():

    num_workers = 4
    today_2025 = str(datetime.now().date()).replace("2024", "2025")
    periods = generate_periods("2024-02-17", today_2025, 14)

    # check which periods still need to be processed by checking the database
    db = Database()
    db.connect()
    raw_acc = db.fetch_data("raw_accommodation")
    db.disconnect()

    # 688 is the number of total locations minus the ones with bad links or countries not serviced by Kayak
    rem_periods = [period for period in periods if raw_acc[raw_acc['start_date'] == period[0].date()].shape[0] < 688]

    with Pool(num_workers) as p:
        p.map(process_period, rem_periods)


if __name__ == "__main__":
    accomodations_main()