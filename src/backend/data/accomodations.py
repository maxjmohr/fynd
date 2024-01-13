from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from bs4 import BeautifulSoup
import numpy as np
from datetime import datetime, timedelta
import time
from tqdm import tqdm
import pandas as pd
import os

global city2code
city2code = {
    "Rome": "c25465"
}

def createURLfromCityAndDate(city, country, dates, num_adults=2):
    """
    Creates a URL for a given city and date.
    Args:
        city (str): The city to search for.
        dates (list): A list of dates in the format YYYY-mm-dd.
    Returns:
        str: The URL for the given city and date.
    """

    # get the city code
    city_code = city2code[city]

    # create and return URL
    return f"https://www.kayak.de/hotels/{city},{country}-{city_code}/{dates[0]}/{dates[1]}/{num_adults}adults?sort=rank_a&attempt=1&lastms=1704637089244"


def getCalendarWeeks(start_date_str, num_weeks):
    """
    Creates a list of calendar weeks starting from a given date.
    Args:
        start_date_str (str): The starting date in the format YYYY-mm-dd.
        num_weeks (int): The number of weeks to create.

    Returns:
        list: A list of tuples (start_date, end_date) for each week.
    """
    # Convert the starting date string to a datetime object
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

    calendar_weeks = []
    for _ in range(num_weeks):
        # Calculate the end date (7 days later)
        end_date = start_date + timedelta(days=6)

        # Append the tuple (start_date, end_date) to the result list
        calendar_weeks.append((start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))

        # Move to the next week
        start_date += timedelta(days=7)

    return calendar_weeks


def getAccomodationPrices(url, slide_width=0.01):
    """
    Gets the number of hotels and the price distribution for a given URL.
    Args:
        url (str): The URL to get the data from.
        slide_width (float): The width of the slider to move.

    Returns:
        tuple: A tuple containing the number of hotels and the price distribution.
    """

    driver = webdriver.Firefox()
    driver.get(url)
    driver.fullscreen_window()

    try:
        consent_button = driver.find_element(By.XPATH, '//div[@class="RxNS-button-content" and text()="Alle ablehnen"]')
        consent_button.click()

    except:
        print("No consent button found")

    time.sleep(5)

    # wait until at least 200 hotels have been loaded
    if int(driver.find_element(By.CLASS_NAME, "yNPo-filtered").text) < 200:
        time.sleep(3)

    slider = driver.find_element(By.XPATH, '//span[@aria-label="Mindestpreis"]')
    assert slider is not None

    orig_soup = BeautifulSoup(driver.page_source, "html.parser")
    n_hotels = int(orig_soup.find(class_="yNPo-filtered").text)
    histogram_heights = [float(bin['style'].split(" ")[1].replace("px;", "")) for bin in orig_soup.find_all(class_="c4yOw")]
    max_price = float(driver.find_element(By.XPATH, '//span[@aria-label="Maximaler Preis"]').get_attribute("aria-valuetext").replace("\xa0€", "").replace(".", ""))

    iterations = len(histogram_heights)
    interval_bounds = []

    for i in range(iterations):
        time.sleep(0.1)

        slider = driver.find_element(By.XPATH, '//span[@aria-label="Mindestpreis"]')
        assert slider is not None

        interval_bounds.append(float(slider.get_attribute("aria-valuetext").replace("\xa0€", "").replace(".", "")))
        actions = ActionChains(driver)
        actions.drag_and_drop_by_offset(slider, slide_width, 0).perform()

    max_price = float(driver.find_element(By.XPATH, '//span[@aria-label="Maximaler Preis"]').get_attribute("aria-valuetext").replace("\xa0€", "").replace(".", ""))
    interval_bounds.append(max_price)

    driver.quit()

    return (n_hotels, histogram_heights, interval_bounds)


def getDistributionStats(bins: list, interval_borders: list):
    """
    Calculates the median and mean of a given distribution.
    Args:
        bins (list): The histogram heights.
        interval_borders (list): The interval borders.
    
    Returns:
        tuple: A tuple containing the median and mean of the distribution.
    """
    # Calculate the midpoint of each interval
    interval_midpoints = [(interval_borders[i] + interval_borders[i + 1]) / 2.0 for i in range(len(interval_borders) - 1)]

    # Calculate the mean of the distribution
    mean = np.average(interval_midpoints, weights=bins)

    # Calculate the cumulative distribution function (CDF)
    cdf = np.cumsum(bins)

    # Find the index of the median value
    median_index = np.searchsorted(cdf, cdf[-1] / 2)

    # Calculate the median based on the interval midpoints
    median = interval_midpoints[median_index]

    return median, mean

def getYearlyAccomodationData(city, country, slide_width=0.01):
    """
    Gets the number of hotels and the price distribution for a given URL.
    Args:
        url (str): The URL to get the data from.
        slide_width (float): The width of the slider to move.
    
    Returns:
        tuple: A tuple containing the number of hotels and the price distribution.
    """

    # create calendar weeks and URLs
    today = datetime.today().strftime('%Y-%m-%d')
    calendar_weeks = getCalendarWeeks(today, 52)
    urls = [createURLfromCityAndDate(city, country, week) for week in calendar_weeks]
    urls = urls[0:1]

    # get the number of hotels and the price distribution for each week
    #hotel_prices = [getAccomodationPrices(url) for url in urls]
    hotel_prices = []
    for url in tqdm(urls):
        time.sleep(0.5)
        n_hotels, histogram_heights, interval_bounds = getAccomodationPrices(url, slide_width=slide_width)
        median, mean = getDistributionStats(histogram_heights, interval_bounds)
        hotel_prices.append((n_hotels, median, mean))

    return hotel_prices


def main():

    os.system("pwd")
    locations = pd.read_csv("./res/master_data/wikivoyage_locations.csv") # load locations
    locations = locations[locations['type'] == "city"] # only cities
    locations = locations.loc[locations['name'] == "Rome"]
    locations = [tuple(x) for x in locations[['name', 'country']].to_numpy()] # convert to list of tuples

    accomodation_prices = {
        'city': [],
        'country': [],
        'n_hotels': [],
        'median': [],
        'mean': []
    }

    for location in tqdm(locations, 'Getting accomodation prices for all locations'):

        data = getYearlyAccomodationData(location[0], location[1])

        for week in data:
            accomodation_prices["city"].append(location[0])
            accomodation_prices["country"].append(location[1])
            accomodation_prices["n_hotels"].append(week[0])
            accomodation_prices["median"].append(week[1])
            accomodation_prices["mean"].append(week[2])

    accomodation_prices = pd.DataFrame(accomodation_prices)
    accomodation_prices.to_csv("./res/master_data/accomodation_prices.csv")


if __name__ == "__main__":
    main()