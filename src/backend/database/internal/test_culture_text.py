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
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import ast

# Clean text by removing unnecessary symbols like HTML tags
CLEANR = re.compile('<.*?>')
replace_str = "S. <em>Aktuelles</em></p><p>"

# Small helper function the clean text
def cleanhtml(raw_html):
    remove_notice = raw_html.replace(replace_str, "")
    cleantext = re.sub(CLEANR, ' ', remove_notice)
    return cleantext

# Function which scrapes the first paragraph on the wikivoyage page of the destinations
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
    driver.find_element(By.XPATH, '/html/body/div[2]/div/div/div[1]/div[2]/div/div[2]/div[3]/div/div[1]/h2/button').click()
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

# Function which collects the top listed attractions on the wikivoyage page for each destination
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
                culture_list = []
                for i in range(10):
                    row_dict = {"location_id" : location_id, "city" : city, "sight" : f"NA"}
                    culture_list.append(row_dict)

                # shut down driver
                driver.close()
                driver.quit()
                return culture_list
            
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
        culture_list = []
        if sum([len(listElem) for listElem in ids]) == 0:
            for i in range(10):
                row_dict = {"location_id" : location_id, "city" : city, "sight" : "NA"}
                culture_list.append(row_dict)
        else:
            for i in range(10):
                for j in range(len(ids)):
                    if len(culture_list) == 10:
                        break
                    if len(ids[j]) < i+1:
                        pass
                    else:
                        row_dict = {"location_id" : location_id, "city" : city, "sight" : ids[j][i]}
                        culture_list.append(row_dict)

    except:
        culture_list = []
        for i in range(10):
            row_dict = {"location_id" : location_id, "city" : city, "sight" : f"NA"}
            culture_list.append(row_dict)

    return culture_list

# Function which collects the current travel warnings issued by the german government
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
            warning_message = f"The German foreign office has issued a travel warning for {country_name}. Additional information available at"
        if warning_type == "Teilreisewarnung":
            warning_message = f"The German foreign office has issued a partial travel warning for {country_name}. Additional information available at"
        warning_link = f"https://www.auswaertiges-amt.de{link}"
        # Save this as a dict, later to be appended to a dataframe
        row_dict = {
            "country_name" : country_name_german,
            "warning_text" : warning_message,
            "link" : warning_link} 
        dict_list.append(row_dict)
        
    travel_warning_df = pd.DataFrame(dict_list)

    # Connect to database
    db = Database()
    db.connect()
    safety_df = db.fetch_data("raw_safety_country")

    # Disconnect from database
    db.disconnect()

    travel_warning_df['country_code'] = None
    for i in range(len(travel_warning_df)):
        for j in range(len(safety_df)):
            if travel_warning_df.loc[i, "country_name"].strip() == safety_df.loc[j, "country_name"].strip():
                travel_warning_df.loc[i, "country_code"] = safety_df.loc[j, "iso2"]

    travel_warning_df = travel_warning_df[travel_warning_df['country_code'].notna()]

    return travel_warning_df


# Function which returns the health information for all countries by the german government
def create_raw_health_texts():

    # Read in dataframe containing the text scraped from the German foreign office
    foreign_office_df = pd.read_csv("res/master_data/foreign_office_df.csv", sep=";")

    # Create database instance and connect to it
    db = Database()
    db.connect()

    # Fetch scores table
    core_scores_df = db.fetch_data("core_locations")
    safety_df = db.fetch_data("raw_safety_country")

    # Disconnect from database
    db.disconnect()

    # Create text dataframe skeleton
    raw_health_text_df = core_scores_df[["location_id", "country_code"]].copy()
    raw_health_text_df["category_id"] = 7

    # Get the information on health from the foreign office df and create list of dicts
    health_rows = []
    for i in foreign_office_df.index:
        health_dict = ast.literal_eval(foreign_office_df.loc[i, "health"])
        health_text_dict = dict()
        if "Current" in health_dict.keys():
            health_text_dict["Current"] = health_dict["Current"]
            del health_dict["Current"]
        if "Vaccination protection" in health_dict.keys():
            health_text_dict["Vaccination protection"] = health_dict["Vaccination protection"]
            del health_dict["Vaccination protection"]
        if "Medical care" in health_dict.keys():
            health_text_dict["Medical care"] = health_dict["Medical care"]
            del health_dict["Medical care"]
        if "General information" in health_dict.keys():
            health_text_dict["General information"] = health_dict["General information"]
            del health_dict["General information"]
        if len(health_dict.keys()) > 0:
            health_text_dict["Health risks"] = list(health_dict.keys())
        health_text_dict["Further information"] = "Further medical information is available at https://www.rki.de/EN/Home/homepage_node.html."
        
        row_dict = {"country_code":foreign_office_df.loc[i, "iso3"], "health_text":health_text_dict}
        health_rows.append(row_dict)

    # Match ISO3 to ISO2 code
    for i in safety_df.index:
        for j in range(len(health_rows)):
            if health_rows[j]["country_code"] == safety_df.loc[i,"iso3"]:
                health_rows[j]["country_code"] = safety_df.loc[i,"iso2"]

    # Assign correct country text to each location
    for i in raw_health_text_df.index:
        for j in range(len(health_rows)):
            if health_rows[j]["country_code"] == raw_health_text_df.loc[i,"country_code"]:
                raw_health_text_df.loc[i,"text"] = str(health_rows[j]["health_text"])

    # Drop country code from final df
    raw_health_text_df.drop("country_code", axis=1)

    return raw_health_text_df


# Function which returns the safety info for all countries by the german government
def create_raw_safety_texts():

    # Read in dataframe containing the text scraped from the German foreign office
    foreign_office_df = pd.read_csv("res/master_data/foreign_office_df.csv", sep=";")

    # Create database instance and connect to it
    db = Database()
    db.connect()

    # Fetch scores table
    core_scores_df = db.fetch_data("core_locations")
    safety_df = db.fetch_data("raw_safety_country")

    # Disconnect from database
    db.disconnect()

    # Create text dataframe skeleton
    raw_safety_text_df = core_scores_df[["location_id", "country_code"]].copy()
    raw_safety_text_df["category_id"] = 7

    # Get the information on safety from the foreign office df and create list of dicts
    safety_rows = []
    for i in foreign_office_df.index:
        safety_dict = ast.literal_eval(foreign_office_df.loc[i, "safety"])
        
        row_dict = {"country_code":foreign_office_df.loc[i, "iso3"], "safety_text":safety_dict}
        safety_rows.append(row_dict)

    # Match ISO3 to ISO2 code
    for i in safety_df.index:
        for j in range(len(safety_rows)):
            if safety_rows[j]["country_code"] == safety_df.loc[i,"iso3"]:
                safety_rows[j]["country_code"] = safety_df.loc[i,"iso2"]

    # Assign correct country text to each location
    for i in raw_safety_text_df.index:
        for j in range(len(safety_rows)):
            if safety_rows[j]["country_code"] == raw_safety_text_df.loc[i,"country_code"]:
                raw_safety_text_df.loc[i,"text"] = str(safety_rows[j]["safety_text"])

    # Drop country code from final df
    raw_safety_text_df.drop("country_code", axis=1)

    return raw_safety_text_df


# Function which returns the money and currency information for all countries by the german government
def create_raw_currency_texts():

    # Read in dataframe containing the text scraped from the German foreign office
    foreign_office_df = pd.read_csv("res/master_data/foreign_office_df.csv", sep=";")

    # Create database instance and connect to it
    db = Database()
    db.connect()

    # Fetch scores and safety tables
    core_scores_df = db.fetch_data("core_locations")
    safety_df = db.fetch_data("raw_safety_country")

    # Disconnect from database
    db.disconnect()

    # Create text dataframe skeleton
    raw_currency_text_df = core_scores_df[["location_id", "country_code"]].copy()
    raw_currency_text_df["category_id"] = 4

    # Get the information on currency from the foreign office df and create list of dicts
    currency_rows = []
    for i in foreign_office_df.index:
        currency_dict = ast.literal_eval(foreign_office_df.loc[i, "travel"])
        currency_text = None

        if "Money/credit cards" in currency_dict.keys():
            currency_text = currency_dict["Money/credit cards"]

        row_dict = {"country_code":foreign_office_df.loc[i, "iso3"], "currency_text":currency_text}
        currency_rows.append(row_dict)

    # Match ISO3 to ISO2 code
    for i in safety_df.index:
        for j in range(len(currency_rows)):
            if currency_rows[j]["country_code"] == safety_df.loc[i,"iso3"]:
                currency_rows[j]["country_code"] = safety_df.loc[i,"iso2"]

    # Assign correct country text to each location
    for i in raw_currency_text_df.index:
        for j in range(len(currency_rows)):
            if currency_rows[j]["country_code"] == raw_currency_text_df.loc[i,"country_code"]:
                raw_currency_text_df.loc[i,"text"] = str(currency_rows[j]["currency_text"])

    # Drop country code from final df
    raw_currency_text_df.drop("country_code", axis=1)

    return raw_currency_text_df


# Function which appends the general info texts to the core_texts table
def insert_general_info_to_core_texts():

    # Create database instance and connect to it
    db = Database()
    db.connect()

    # Fetch general info texts table data
    gen_info_texts = db.fetch_data("raw_general_info_texts")

    # Disconnect from database
    db.disconnect()

    # Add columns to gen_info_texts dataframe to match structure of core_texts
    gen_info_texts.insert(2, "start_date", "2023-01-01")
    gen_info_texts.insert(3, "end_date", "2099-12-31")
    gen_info_texts.insert(4, "ref_start_location_id", -1)
    gen_info_texts.insert(6, "text_anomaly", None)
    gen_info_texts.rename(columns={"text":"text_general"}, inplace=True)
    gen_info_texts["updated_at"] = pd.to_datetime('today')
    gen_info_texts = gen_info_texts[gen_info_texts["text_general"].notna()]

    # Connect to db
    db.connect()

    # Append general info text to core_texts
    db.insert_data(gen_info_texts, "core_texts", if_exists="append")

    # Disconnect from database
    db.disconnect()

