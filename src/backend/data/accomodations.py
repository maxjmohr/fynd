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
import sys
import requests
import json
from unidecode import unidecode

from multiprocessing import Pool

# import database class from database module located in src/backend
sys.path.append("./src/backend")
from database.db_helpers import Database

MAX_RETRIES = 80
SLEEP_TIMER = 300
COUNTER = 0
    

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

    loc_json = parseLocationJSON(city, country, mode=mode)

    if loc_json is None:
        return None
        
    city_id, country, city = loc_json['city_id'], country.replace(" ", "-"), city.replace(" ", "-")

    return f"https://www.kayak.com/hotels/{city},{country}-c{city_id}/{dates[0]}/{dates[1]}/{num_adults}adults?sort=rank_a"


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
    

def getAccommodationData(kayak_url, driver):
    """
    Gets the counts, interval bounds and the average price from a search request URL
    args:
        url: The URL of the search request
    returns:
        count: The number of hotels in the search request
        interval_bounds: The interval bounds of the price filter
        average_price: The average price of the hotels in the search request
    """
    
    driver.get(kayak_url)

    # Check for the presence of the security check element
    try:
        driver.find_element(By.CSS_SELECTOR, '.WZTU-wrap')
        print("Security check detected")
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
        n_props = int(driver.find_element(By.CSS_SELECTOR, '.gfww').text.replace(" results", ""))
        if n_props == "0 properties":
            return 0

    except:
        pass

    browser_log = driver.get_log('performance') 
    events = [json.loads(entry['message'])['message'] for entry in browser_log]
    _ = driver.get_log('browser') # Clear the logs after each successful poll request

    # Filter events
    events = [event for event in events if 'Network.response' in event['method']]
    poll_events = []
    for event in events:
        try:
            url = event['params']['response']['url']
            if url == "https://www.kayak.com/i/api/search/dynamic/hotels/poll":
                poll_events.append(event)
            
        except:
            pass
    
    # Only keep the one with the latest timestamp
    poll_events.sort(key=lambda x: x['params']['timestamp'])

    try:
        last_rec = poll_events[-1]
        response = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': last_rec["params"]["requestId"]})
        body = json.loads(response['body'])

        return body

    except:

        print(f"Could not get response body for {kayak_url} (No matching response found).")
        return None
    

def parseAccommodationData(json_body):
    
    acc_data = {}

    # check for valid response from getAccommodationData()
    if isinstance(json_body, dict):

        # CASE 1: histogram visible and request to get histogram data successful
        if 'totalCount' in json_body:
    
            acc_data['n_hotels'] = json_body['totalCount']

            if acc_data['n_hotels'] == 0:
                acc_data['avg_price'] = np.nan
                acc_data['comp_avg'] = np.nan
                acc_data['comp_median'] = np.nan

                for i in range(30):
                    acc_data[f"bin_height_{i+1}"] = np.nan
                    acc_data[f"bin_bound_{i+1}"] = np.nan

                acc_data['bin_bound_31'] = np.nan

                return acc_data
            
            else:

                assert json_body['priceMode'] == "total"

                if 'price' in json_body['filterData']:

                    # for some locations only one price bin is returned
                    if len(json_body['filterData']['price']['count']) > 1:

                        acc_data['avg_price'] = json_body['filterData']['price']['averagePrice']['price']

                        for i, v in enumerate(json_body['filterData']['price']['values']):
                            acc_data[f"bin_bound_{i+1}"] = v

                        for i, v in enumerate(json_body['filterData']['price']['count']):
                            acc_data[f"bin_height_{i+1}"] = v

                        # compute median and average from the scraped bins
                        bin_heights = json_body['filterData']['price']['count']
                        bin_bounds = json_body['filterData']['price']['values']
                        acc_data['comp_median'], acc_data['comp_avg'] = calculate_median_average(bin_bounds, bin_heights)

                        return acc_data
                    
                    else:
                        acc_data['avg_price'] = json_body['filterData']['price']['averagePrice']['price']

                        # fill bin data with NaN
                        for i in range(30):
                            acc_data[f"bin_height_{i+1}"] = np.nan
                            acc_data[f"bin_bound_{i+1}"] = np.nan

                        acc_data['bin_bound_31'] = np.nan

                        # replace first bin height with average price and replace bounds with returned bounds (2 total bounds)
                        acc_data['bin_height_1'] = acc_data['avg_price']
                        for i, bound in enumerate(json_body['filterData']['price']['values']): acc_data[f'bin_bound_{i+1}'] = bound

                        # set computed median and computed average to returned average and return dict
                        acc_data['comp_median'], acc_data['comp_avg'] = acc_data['avg_price'], acc_data['avg_price'] 
                        return acc_data
                
                # for some locations none of the hotels have a price, but there are hotels
                elif ('price' not in json_body['filterData']) and ('totalCount' in json_body):
                    acc_data['n_hotels'] = json_body['totalCount']
                    acc_data['avg_price'] = np.nan
                    acc_data['comp_avg'] = np.nan
                    acc_data['comp_median'] = np.nan

                    for i in range(30):
                        acc_data[f"bin_height_{i+1}"] = np.nan
                        acc_data[f"bin_bound_{i+1}"] = np.nan

                    acc_data['bin_bound_31'] = np.nan

                    return acc_data
                
                else:
                    print(json_body['filterData'].keys())
                    return None
                
    else:
        print("Unable to parse non-dict return value.")
        return None
    

def configureChromeDriver(headless=False):
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument('--window-size=720,480')
    if headless: options.add_argument("--headless")

    return caps, options
    

def process_period(period):

    # convert periods to string
    period = [period[0].strftime("%Y-%m-%d"), period[1].strftime("%Y-%m-%d")]

    # configuration of parameters
    cur_country, driver = None, None
    caps, options = configureChromeDriver()

    db = Database()
    db.connect()
    locations = db.fetch_data("core_locations")[['location_id', 'city', 'country']]
    raw_acc = db.fetch_data("raw_accommodation_costs")
    db.disconnect()

    # select rows from database that have start_date and end_date equal to the current period
    raw_acc = raw_acc[(pd.to_datetime(raw_acc['start_date']) == pd.to_datetime(period[0])) 
                        & (pd.to_datetime(raw_acc['end_date']) == pd.to_datetime(period[1]))]

    ### -------- LOCATION FILTERING AND PREPROCESSING -------- ###

    # some locations not serviced by Kayak
    bad_locations = [
        ['Chattogram', 'Bangladesh'],
        ['Jashore', 'Bangladesh'],
        ['Mymensingh', 'Bangladesh'],
        ['San Francisco Gotera', 'El Salvador'],
        ['Ar Rutbah', 'Iraq'],
        ['Fallujah', 'Iraq'],
        ['Al Salt', 'Jordan'],
        ['Mubarak Al-Kabeer', 'Kuwait'],
        ['Shahhat', 'Libya'],
        ['Tubruq', 'Libya'],
        ['Dukhan', 'Qatar']
    ]

    # extend bad locations by countries not serviced by Kayak due to government restrictions
    for country in ["Belarus", "Russia", "Iran"]:
        bad_locations.extend(locations[locations['country'] == country][['city', 'country']].values.tolist())

    # read in translations for locations with bad names
    with open("./res/master_data/location_rename.json", "r", encoding="utf-8") as f:
        location_rename = json.load(f)

    # select only locations that have not been processed yet
    processed_locs = raw_acc['location_id'].values.tolist()
    locations = locations[~locations['location_id'].isin(processed_locs)]
    
    # rename some country and location names to fit Kayaks names
    locations.loc[locations['country'] == "Czechia", 'country'] = "Czech Republic" # replace values of "Czechia" with "Czech Repulic"
    locations.loc[locations['location_id'] == 206579565, 'city'] = "Hong Kong"
    locations.loc[locations['location_id'] == 206579565, 'country'] = "Hong Kong"    
    #locations['city'] = locations[['city', 'country']].apply(lambda x: location_rename[f"{x['city']}, {x['country']}"] if f"{x['city']}, {x['country']}" in location_rename.keys() else x['city'],  axis=1)

    print(f"{len(locations)} missing locations for period {period}...")

    #locations = locations.sort_values(by='country', ascending=False) # from Z to A

    ### -------------------------------------------------- ###
    
    counter = COUNTER

    # loop through loc_id, city, country triplets
    for loc_id, city, country in tqdm(locations.values):
        print(f"Processing {city}, {country} for period {period}...")

        # rename city if it is in the location_rename dictionary
        city = location_rename[f"{city}, {country}"] if f"{city}, {country}" in location_rename.keys() else city

        # insert row containing no accommodation price data if location is in list of bad locations
        if [city, country] in bad_locations:
            acc_data = {}
            acc_data['location_id'] = loc_id
            acc_data['kayak_city'], acc_data['kayak_country'] = city, country
            acc_data['start_date'], acc_data['end_date'] = period[0], period[1]
            acc_data['n_hotels'] = np.nan
            acc_data['avg_price'] = np.nan
            acc_data['comp_avg'] = np.nan
            acc_data['comp_median'] = np.nan

            for i in range(30):
                acc_data[f"bin_height_{i+1}"] = np.nan
                acc_data[f"bin_bound_{i+1}"] = np.nan

            acc_data['bin_bound_31'] = np.nan

            db.connect()
            db.insert_data(pd.DataFrame(acc_data, index=[0]), "raw_accommodation_costs")
            db.disconnect()
            continue

        # start a new driver for each country
        if cur_country != country:
            if driver:
                driver.quit()
            cur_country = country
            driver = webdriver.Chrome(desired_capabilities=caps, options=options)

        url = createURLfromCityAndDate(city.split("/")[0].strip(), country, period)

        if url is None:
            print(f"Could not get URL for {city}, {country}")
            continue
 
        json_body = getAccommodationData(url, driver)

        # if getAccommodationData() returns -1, there was a security check
        if json_body == -1:
            print(f"Security check detected for {city}, {country}. Returning and sleeping for 180 seconds")
            if driver:
                driver.quit()
            time.sleep(SLEEP_TIMER)
            counter = COUNTER

        # if getAccommodationData() returns None, there was an error getting the response
        elif json_body is None:
            print(f"Could not get data for {city}, {country}")
            counter += 1

            if counter >= MAX_RETRIES:
                print("Maximum number of retries reached, skipping...")
                counter = COUNTER
                if driver:
                    driver.quit()

        # in all other cases (0 and actual data), parse the data and insert it into the database
        else:
            acc_data = parseAccommodationData(json_body)

            if acc_data is not None:
                total_booking_days = (getDaysBetweenDates(period[0], period[1]) + 1)
                acc_data['location_id'] = loc_id
                acc_data['kayak_city'], acc_data['kayak_country'] = city, country
                acc_data['start_date'], acc_data['end_date'] = period[0], period[1]
                acc_data['avg_price'] = acc_data['avg_price'] / total_booking_days
                acc_data['comp_avg'], acc_data['comp_median'] = acc_data['comp_avg']/total_booking_days, acc_data['comp_median']/total_booking_days
                db.connect()
                db.insert_data(pd.DataFrame(acc_data, index=[0]), "raw_accommodation_costs")
                db.disconnect()    

            else:
                print(f"Could not parse data for {city}, {country} ({period})")

    if driver:
        driver.quit()  

    return None