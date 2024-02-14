import requests
import re
from deep_translator import GoogleTranslator
import pandas as pd
from textwrap import wrap

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.firefox.options import Options
import time

# Clean text by removing unnecessary symbols like HTML tags
CLEANR = re.compile('<.*?>')
replace_str = "S. <em>Aktuelles</em></p><p>"

# Small helper function the clean text
def cleanhtml(raw_html):
    remove_notice = raw_html.replace(replace_str, "")
    cleantext = re.sub(CLEANR, ' ', remove_notice)
    return cleantext

# Queries the website of the german foreign office and extracts the unique country code needed to access the travel information
def get_aa_codes():

    # import german country names from excel file
    de_country_codes = pd.read_excel("../../../res/master_data/de_country_codes.xlsx")

    # make browser headless
    options = Options()
    options.headless = True
    dict_list = []

    # iterate over countries in excel
    for i in range(len(de_country_codes)):
        country = de_country_codes.loc[i,"Kurzform"]
        iso3 = de_country_codes.loc[i,"Code (3)"]
        # open Firefox
        driver = webdriver.Firefox(options=options)
        # open page of german foreign office
        driver.get("https://www.auswaertiges-amt.de/de/ReiseUndSicherheit/reise-und-sicherheitshinweise?openAccordionId=item-199348-1-panel")
        # go to search field
        typetextfirst = driver.find_element(By.ID, "search-input-350334")
        # search for country and load country specific page
        typetextfirst.clear()
        typetextfirst.send_keys(country)
        typetextfirst.send_keys(Keys.RETURN)
        # wait for site to load
        time.sleep(3)
        # return url
        get_url = driver.current_url
        url_parts = str.split(get_url, sep="/")
        row_dict = {'country' : country, 'iso3' : iso3, 'aa_code' : url_parts[-1]}
        dict_list.append(row_dict)
        # stop driver
        driver.quit()

    # create dataframe, save in csv
    country_german_code_df = pd.DataFrame.from_dict(dict_list)
    country_german_code_df.to_csv("../../../res/master_data/country_codes_auswaertiges_amt.csv")


# Function wrapper for the process of aquiring information on health and other travel information on countries
def get_health_info():
    # Dict for paragraph headlines that need to be extracted
    paragraph_dict = {"Sicherheit":"safety",
                    "Natur und Klima":"climate",
                    "Reiseinfos":"travel",
                    "Einreise und Zoll":"entry",
                    "Gesundheit":"health",
                    }

    # Takes country_id from german foreign office, extracts info text from websites and splits it into paragraphs
    def generate_reports(aa_id):

        # Dictionary where all paragraphs will be stored later
        reports_dict = {}

        # For every paragraph headline
        for key,value in paragraph_dict.items():

            # Set up dictionary for this paragraphy, which collects all text parts
            section_dict={}

            # Get content from website
            travel_warning = requests.get("https://www.auswaertiges-amt.de/opendata/travelwarning/" + aa_id)
            
            # Extract text from website content
            search_text = travel_warning.text

            # Search for paragraph in the text
            safety = re.search('<h2>.{0,20}'+key+'.{0,40}</h2>(.*?)<h2>(.*)</h2>', search_text)

            # For some countries, the paragraph "Natur und Klima" is instead named "Naturkatastrophen"
            if key=="Natur und Klima":
                if safety is None:
                    safety = re.search('<h2>.{0,20}'+"Naturkatastrophen"+'.{0,20}</h2>(.*?)<h2>(.*)</h2>', search_text)

            # Split paragraph into multiple sections, if there are <h3> headings in the text
            safety_split = re.split(r'<h3>(.*?)</h3>', safety.group(1))

            # Remove empty sections and unneeded headline tags
            try:
                safety_split.remove("")
            except:
                pass

            try:
                safety_split.remove("</h2>")
            except:
                pass        
            
            # If the length of sections is not even, the first section contains current info, which doesn't get a headline
            if len(safety_split)%2 != 0:
                # Insert additional headline
                safety_split.insert(0, "Allgemeine Informationen")
            # For every pair of headline and section
            for i in range(0, len(safety_split), 2):
                # If a section is longer than 5000 words, the translator will not work
                if len(cleanhtml(safety_split[i+1])) > 5000:
                    # In that case, split the section into multiple parts, translate them seperately, put them back together
                    s = cleanhtml(safety_split[i+1])
                    s_parts = wrap(s, 5000)
                    translated = ""
                    for part in s_parts:
                        part_trans = GoogleTranslator(target='en').translate(part)
                        translated = translated + part_trans
                    section_dict[GoogleTranslator(target='en').translate(cleanhtml(safety_split[i]))] = translated
                # If not, just translate it to English in one piece
                else:
                    section_dict[GoogleTranslator(target='en').translate(cleanhtml(safety_split[i]))] = \
                        GoogleTranslator(target='en').translate(cleanhtml(safety_split[i+1]))

            # Add paragraph to dict with headline as key
            reports_dict[value]=section_dict

        return reports_dict

    # Read in the dataframe containing the aa_codes
    aa_country_codes_df = pd.read_csv("../../../res/master_data/country_codes_auswaertiges_amt.csv", sep=";").drop("Unnamed: 0", axis=1)
    aa_country_codes_df["aa_code"] = aa_country_codes_df["aa_code"].astype('int').astype('str')

    
    dict_list = []
    # For every country
    for i in range(len(aa_country_codes_df)):
        # Print name of the country currently being scraped
        print(f"Currently gathering information for {aa_country_codes_df.iloc[i]['country']}.")
        # Call helper function the generate the report
        safety_dict = generate_reports(aa_country_codes_df.iloc[i]["aa_code"])
        # Save country information in a dictionary
        row_dict = {"iso3" : aa_country_codes_df.iloc[i]["iso3"],
                    "country_name" : str(aa_country_codes_df.iloc[i]["country"]),
                    "safety" : str(safety_dict["safety"]),
                    "nature_climate" : str(safety_dict["climate"]),
                    "travel" : str(safety_dict["travel"]),
                    "entry" : str(safety_dict["entry"]),
                    "health" : str(safety_dict["health"])}
        # Save dict in a list
        dict_list.append(row_dict)
        # For every 20 countries, save the intermediate result, in case of crashes in the connection
        if i % 20 == 0:
            health_df = pd.DataFrame.from_dict(dict_list)
            health_df.to_csv("../../../res/master_data/health_info.csv")

    # Make dataframe out of dict, append info on Germany by calling separate function
    health_df = pd.DataFrame.from_dict(dict_list)
    health_info_germany = get_germany_info()
    health_df.loc[len(health_df.index)] = ['DEU', "Germany", "None", "None", "None", "None", str(health_info_germany)]  

    # Save the final result in a csv
    health_df.to_csv("../../../res/master_data/health_info.csv")


# Function to get travel info about Germany, since the German foreign office doesn't have info on the country itself
def get_germany_info():
    # Get travel adivsory from US foreign office
    travel_warning = requests.get("https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/Germany.html")
    t_text = travel_warning.text

    # Clean text
    clean_str = str(cleanhtml(t_text))

    # Find section about health
    german_health_info = re.findall("COVID-19 Vaccines:(.*)Travel and Transportation", clean_str, re.DOTALL)[0]

    # Remove unnecessary characters
    to_be_replaced = ["\u202f", "&nbsp;", "\r", "\n"]
    for str_rep in to_be_replaced:
        german_health_info = german_health_info.replace(str_rep, "")

    german_health_info = "COVID-19 Vaccines: " + german_health_info

    german_dict = {"General Information:" : german_health_info}

    return german_dict

# Function which generates a dataframe containing country names and their health score according to the Legatum Prosperity Index and returns them
def get_legatum_health_score():
    # set up selenium driver
    options = Options()
    options.headless = True
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Firefox(options=options)
    driver.get("https://www.prosperity.com/rankings")

    # move slider to "score" instead of "rank"
    score_slider = driver.find_element(By.XPATH, '//*[@id="rank_score_btn-thumb-0"]')
    move = ActionChains(driver)
    move.click_and_hold(score_slider).move_by_offset(100, 0).release().perform()
    time.sleep(3)

    # copy table data
    legatum_raw_table = driver.find_element(By.XPATH, '//*[@id="treeview-1032"]')

    # split resulting text so that every table element is its own list element
    legatum_raw_scores = legatum_raw_table.text.split(sep="\n")

    # shut down driver
    driver.close()
    driver.quit()

    # get elements at 2nd and 12th position of each table row, which correspond to the country name and health score
    countries = []
    health_scores = []
    for i in range(len(legatum_raw_scores)):
        if i % 14 == 1:
            countries.append(legatum_raw_scores[i])
        if i % 14 == 11:
            health_scores.append(legatum_raw_scores[i])

    # create dataframe and return it
    health_score_df = pd.DataFrame({"country_name" : countries,
                                    "health_score": health_scores})
    
    return health_score_df

# Function to get travel info about Germany, since the German foreign office doesn't have info on the country itself
def get_germany_info_safety():
    # Get travel adivsory from US foreign office
    travel_warning = requests.get("https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/Germany.html")
    t_text = travel_warning.text

    # Clean text
    clean_str = str(cleanhtml(t_text))

    # Find sections about terrorism and crime information
    safety_info = re.findall("Safety and Security(.*)Local Laws & Special Circumstances", clean_str, re.DOTALL)[0]
    terrorism_info = re.findall("Terrorism:(.*)For more information, see our  Terrorism  page.", safety_info, re.DOTALL)[0]
    crime_info = re.findall("Crime:(.*)Victims of Crime", safety_info, re.DOTALL)[0]

    # Remove unnecessary characters
    to_be_replaced = ["\u202f", "&nbsp;", "\r", "\n"]
    for str_rep in to_be_replaced:
        terrorism_info = terrorism_info.replace(str_rep, "")
        crime_info = crime_info.replace(str_rep, "")

    german_dict = {"terrorism" : terrorism_info, "crime" : crime_info}

    return german_dict