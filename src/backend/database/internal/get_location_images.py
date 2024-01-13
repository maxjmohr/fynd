import os
import sys
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

import pandas as pd
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import time
import pyperclip
from database.db_helpers import Database

# set up selenium driver
options = Options()
options.headless = True
options.add_argument('--disable-blink-features=AutomationControlled')


dict_list = []
def get_location_image(location_id, city, country):
    time.sleep(3)
    # open wikipedia page
    driver = webdriver.Firefox(options=options)
    driver.get("https://en.wikipedia.org/wiki/Main_Page")
    time.sleep(5)
    try:

        # go to search field
        location_search = driver.find_element(By.NAME, "search")

        # search for location
        location_search.clear()
        location_search.send_keys(f"{city}, {country}")
        time.sleep(2)
        driver.find_element(By.XPATH, "/html/body/div[2]/header/div[2]/div/div/div/form/div/button").click()
        time.sleep(2)

        if "search" in driver.current_url:
            # get link to first search result, click it to load location wiki page
            results = driver.find_element(By.XPATH, """/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[2]
                                        /div[4]/ul/li[1]/table/tbody/tr/td[2]/div[1]/a/span""")
            results.click()
            time.sleep(4)

        try:
            div_imgs = driver.find_element(By.XPATH, "/html/body/div[3]/div/div[3]/main/div[3]/div[3]/div[1]/table/tbody/tr[3]/td")
        except selenium.common.exceptions.NoSuchElementException:
            div_imgs = driver.find_element(By.XPATH, "/html/body/div[3]/div/div[3]/main/div[3]/div[3]/div[1]/table[1]/tbody/tr[3]/td")

        imgs = div_imgs.find_elements(By.TAG_NAME, "img")
        time.sleep(1)
        imgs[0].click()
        time.sleep(2)

        # Click on Download button to get to author information
        download = driver.find_element(By.XPATH, """/html/body/div[7]/div/div[1]/a[1]""")
        download.click()
        time.sleep(1)

        # Click on "Attribute" button to get quote
        attribute = driver.find_element(By.XPATH, """/html/body/div[7]/div/div[2]/div/div[3]/div[3]/div[2]/div[1]/p[1]""")
        attribute.click()
        time.sleep(1)

        # Copy text such that the author of the image can be credited
        source = driver.find_element(By.XPATH, """/html/body/div[7]/div/div[2]/div/div[3]/div[3]/
                                        div[2]/div[2]/div[1]/div/div/span/span/a/span[1]""")
        source.click()
        src_text = pyperclip.paste()
        time.sleep(1)

        # Open image in full screen for best resolution
        img = driver.find_element(By.XPATH, "/html/body/div[7]/div/div[2]/div/div[1]/img")
        img.click()
        img.click()
        img_url = driver.current_url
        row_dict = {"location_id" : location_id, "img_url" : img_url, "source" : src_text}
        dict_list.append(row_dict)

    except:
        row_dict = {"location_id" : location_id, "img_url" : "NA", "source" : "NA"}
        dict_list.append(row_dict)
        
    finally:
        # wait for site to load
        time.sleep(2)
        # stop driver
        driver.close()
        driver.quit()


# Get image links and sources for all locations in database
""" for i in range(len(locations_df)):
    get_location_image(locations_df.loc[i, "location_id"], locations_df.loc[i, "city"], locations_df.loc[i, "country"])

    if i % 20 == 0:
        location_images_df = pd.DataFrame.from_dict(dict_list)
        location_images_df.to_csv("res/master_data/location_images.csv")

location_images_df = pd.DataFrame.from_dict(dict_list)
location_images_df.to_csv("res/master_data/location_images.csv") """

# Load CSV into database
""" locations_images_df = pd.read_csv("res/master_data/locations_images.csv", sep=";")
locations_images_df.drop("Unnamed: 0", axis=1)
column_order = ["location_id", "img_url", "source"]
locations_images_df = locations_images_df.reindex(columns=column_order)

# Connect to database
db = Database()
db.connect()
db.create_db_object("core_locations_images", drop_if_exists=True)
db.insert_data(locations_images_df, "core_locations_images", if_exists="append", updated_at=True)

# Disconnect from database
db.disconnect() """