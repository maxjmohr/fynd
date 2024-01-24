import os
import sys
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)
from database.db_helpers import Database

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import time
import requests
import re
from textwrap import wrap
from bs4 import BeautifulSoup
import itertools
from deep_translator import GoogleTranslator

# Clean text by removing unnecessary symbols like HTML tags
CLEANR = re.compile('<.*?>')
replace_str = "S. <em>Aktuelles</em></p><p>"

# Small helper function the clean text
def cleanhtml(raw_html):
    remove_notice = raw_html.replace(replace_str, "")
    cleantext = re.sub(CLEANR, ' ', remove_notice)
    return cleantext


# Connect to database
db = Database()
db.connect()
foreign_office_df = db.fetch_data("raw_health")
# Disconnect from database
db.disconnect()

def get_info_text(location_id, city):
    # set up selenium driver
    options = Options()
    options.headless = True
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Firefox(options=options)
    driver.get("https://en.wikivoyage.org/wiki/Main_Page")
    time.sleep(2)

    # go to search field
    location_search = driver.find_element(By.NAME, "search")
    # search for location
    location_search.clear()
    location_search.send_keys(f'{city}')
    time.sleep(2)
    driver.find_element(By.XPATH, '/html/body/div[3]/div[3]/div[5]/div[1]/div[1]/div[1]/div[1]/div/div/form/input[2]').click()
    time.sleep(2)

    if "Search" in driver.current_url:
            # get link to first search result, click it to load location wiki page
            try:
                driver.find_element(By.XPATH, """/html/body/div[3]/div[3]/div[4]/div[2]/
                                            div[3]/ul/li[1]/div[1]/a/span""").click()
                time.sleep(2)
            except:
                 row_dict = {"location_id" : location_id, "city" : city, "general_info_text" : "NA"}
                 return row_dict

    try:
        general_info_text = driver.find_element(By.XPATH, '/html/body/div[3]/div[3]/div[5]/div[1]/p[2]').text
    except:
         pass
    try:
        general_info_text = driver.find_element(By.XPATH, '/html/body/div[3]/div[3]/div[5]/div[1]/p').text
    except:
        pass
    try:
        general_info_text = driver.find_element(By.XPATH, '/html/body/div[3]/div[3]/div[5]/div[1]/p[2]').text
    except:
         pass
            
    time.sleep(2)

    # shut down driver
    driver.close()
    driver.quit()

    row_dict = {"location_id" : location_id, "city" : city, "general_info_text" : general_info_text}
    
    return row_dict

""" dict_list = []
for i in range(len(locations_df)):
    row_dict = get_info_text(location_id=locations_df.loc[i, "location_id"], city=locations_df.loc[i, "city"])
    dict_list.append(row_dict)
    if i % 10 == 0:
        location_info_text_df = pd.DataFrame(dict_list)
        location_info_text_df.to_csv("res/master_data/location_info_text_2.csv")
location_info_text_df = pd.DataFrame(dict_list)
location_info_text_df.to_csv("res/master_data/location_info_text_2.csv") """

def get_culture_text(location_id, city):

    # set up selenium driver
    options = Options()
    options.headless = True
    options.add_argument('--disable-blink-features=AutomationControlled')

    driver = webdriver.Firefox(options=options)
    driver.get("https://en.wikivoyage.org/wiki/Main_Page")
    time.sleep(2)

    # go to search field
    location_search = driver.find_element(By.NAME, "search")
    # search for location
    location_search.clear()
    location_search.send_keys(f'{city}')
    time.sleep(2)
    driver.find_element(By.XPATH, '/html/body/div[3]/div[3]/div[5]/div[1]/div[1]/div[1]/div[1]/div/div/form/input[2]').click()
    time.sleep(2)

    if "Search" in driver.current_url:
            # get link to first search result, click it to load location wiki page
            try:
                driver.find_element(By.XPATH, """/html/body/div[3]/div[3]/div[4]/div[2]/
                                            div[3]/ul/li[1]/div[1]/a/span""").click()
                time.sleep(2)
            except:
                 row_dict = {"location_id" : location_id, "city" : city, "culture_text" : "NA"}
                     # shut down driver
                 driver.close()
                 driver.quit()
                 return row_dict
            
    # Get content from website
    search_text = driver.page_source

    # shut down driver
    driver.close()
    driver.quit()

    # Search for paragraph in the text, extract tables
    try:
        section_test = re.findall(r'<span class="mw-headline" id="See">See</span>[\s\S]+?<h2><span class="mw-headline"', search_text)
        soup = BeautifulSoup(section_test[0], features="lxml")
        paragraphs = soup.findAll('p')
        lists = soup.findAll('ul')
        ids = []
        # For each table, find the names of the landmarks and save them in a list
        for l in lists:
            to_drop = []
            places = re.findall(r'id=".+?"',str(l))
            replace_chars = {"_":" ", "/":""}
            for i in range(len(places)):
                places[i] = places[i][4:-1]
                for char in replace_chars.keys():
                    places[i] = places[i].replace(char, replace_chars[char])
                digit_count = 0
                for j in places[i]:
                    if j.isdigit():
                        digit_count += 1
                if digit_count > 3:
                    to_drop.append(i) 
            filtered_places = list(filter(lambda x: places.index(x) not in to_drop, places))
            ids.append(filtered_places)
        culture_list = list(itertools.chain.from_iterable(ids))
        print(culture_list)
        row_dict = {"location_id" : location_id, "city" : city, "culture_text" : culture_list}
    except:
        row_dict = {"location_id" : location_id, "city" : city, "culture_text" : "NA"}

    return row_dict

def get_travel_warnings():
    # From website of German foreign office, extract information about travel warnings
    travel_warning = requests.get("https://www.auswaertiges-amt.de/de/ReiseUndSicherheit/10.2.8Reisewarnungen")
    soup = BeautifulSoup(travel_warning.content, "html.parser")

    # Find list containing countries
    travel_warning_list = soup.select('ul.rte__unordered-list')

    dict_list = []

    #For each list element, get country name and type of travel warning to create a text
    for warning in travel_warning_list[0].find_all('li'):
        link = warning.find_all('a', href=True)[0]["href"]
        country_name_german = warning.text.split(":")[0]
        warning_type = warning.text.split("(")[-1][:-1]
        country_name = GoogleTranslator(target='en').translate(country_name_german)
        if warning_type == "Reisewarnung":
            warning_message = f"The German foreign office has issued a travel warning for {country_name}. Additional information available at https://www.auswaertiges-amt.de{link}."
        if warning_type == "Teilreisewarnung":
            warning_message = f"The German foreign office has issued a partial travel warning for {country_name}. Additional information available at https://www.auswaertiges-amt.de{link}."
        
        # Save this as a dict, later to be appended to a dataframe
        row_dict = {
            "country_name" : country_name_german,
            "warning" : warning_message} 
        dict_list.append(row_dict)
        
    travel_warning_df = pd.DataFrame(dict_list)

    return travel_warning_df

travel_warning_df = get_travel_warnings()

travel_warning_df.to_csv("res/master_data/travel_warnings_df.csv")
""" dict_list = []
for i in range(661, len(locations_df)):
     row_dict = get_culture_text(locations_df.loc[i, "location_id"], locations_df.loc[i, "city"])
     dict_list.append(row_dict)
     if i % 10 == 0:
          culture_text_df = pd.DataFrame(dict_list)
          culture_text_df.to_csv("res/master_data/culture_text_2.csv")

culture_text_df = pd.DataFrame(dict_list)
culture_text_df.to_csv("res/master_data/culture_text_2.csv") """

""" category_dict = {
                 "0" : 'General info text',
                 "1" : 'Safety text',
                 "2" : 'Weather text',
                 "3" : 'Culture text',
                 "4" : 'Cost text',
                 "5" : 'Geography text',
                 "6" : 'Reachability text',
                 "7" : 'Health text'
                 }

dict_list = []
for i in range(len(locations_df)):
    for key, val in category_dict.items():
        row_dict = {"location_id":locations_df.loc[i,"location_id"],
                    "category_id":key,
                    "start_date": "2024-01-01",
                    "end_date":	"2099-12-31",
                    "reference_start_location":"Tübingen",
                    "text" : f'{val} on {locations_df.loc[i,"city"]}.'
                    }
        dict_list.append(row_dict)

texts_df = pd.DataFrame(dict_list) """ 

""" # Connect to database
db = Database()

db.connect()
db.create_db_object("raw_culture_texts", drop_if_exists=True)
db.insert_data(general_info_df, "raw_culture_texts", if_exists="append", updated_at=True)

# Disconnect from database
db.disconnect() """