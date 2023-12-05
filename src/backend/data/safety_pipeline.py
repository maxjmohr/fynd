import requests
from bs4 import BeautifulSoup
import re

import spacy
from spacy.lang.de.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest

import json
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)



#safe place api --> free version only has limited number of cities

""" # initialize using parameters
amadeus = Client(client_id=client_id, client_secret=client_secret)
try:
    # returns safety information for a location based on geolocation coordinates (e.g. Berlin)
    response = amadeus.safety.safety_rated_locations.by_square.get(
        north=45.397158,
        west=7.160873,
        south=40.394582,
        east=20.177181)
    print(response.data)
except ResponseError as error:
    raise error """

# for select cities, the Teleport API offers city specific safety scores. When available, 
# this score can supplement/supercede the country score
def create_city_safety_df(city):
    #call API for city
    api_string = "https://api.teleport.org/api/urban_areas/slug:" + city.lower() + "/scores/"
    city_safety = requests.get(api_string)

    # if scores are not available for this city, return empty dataframe
    if str(city_safety) == "<Response [404]>":
        city_safety_df = pd.DataFrame({'A' : []})
    else:
        # convert scores per category into dataframe
        city_safety_df = pd.DataFrame.from_dict(city_safety.json()["categories"])


        #city_safety_df = city_safety_df.drop(columns=["color"])

        # rename columns
        city_safety_df = city_safety_df.rename(columns={"name":"Category", "score_out_of_10":"ScoreOutOf10"})

    return city_safety_df

# travel advisory --> scores inacurate
""" country_travel_warning = requests.get("https://www.travel-advisory.info/api")
print(country_travel_warning.text) """

countries = requests.get("https://www.auswaertiges-amt.de/opendata/travelwarning")
#print(countries.text)

#copied function that summarizes a given text by some percentage
def summarize(text, per):
    nlp = spacy.load('de_core_news_sm')
    doc= nlp(text)
    tokens=[token.text for token in doc]
    word_frequencies={}
    for word in doc:
        if word.text.lower() not in list(STOP_WORDS):
            if word.text.lower() not in punctuation:
                if word.text not in word_frequencies.keys():
                    word_frequencies[word.text] = 1
                else:
                    word_frequencies[word.text] += 1
    max_frequency=max(word_frequencies.values())
    for word in word_frequencies.keys():
        word_frequencies[word]=word_frequencies[word]/max_frequency
    sentence_tokens= [sent for sent in doc.sents]
    sentence_scores = {}
    for sent in sentence_tokens:
        for word in sent:
            if word.text.lower() in word_frequencies.keys():
                if sent not in sentence_scores.keys():                            
                    sentence_scores[sent]=word_frequencies[word.text.lower()]
                else:
                    sentence_scores[sent]+=word_frequencies[word.text.lower()]
    select_length=int(len(sentence_tokens)*per)
    summary=nlargest(select_length, sentence_scores,key=sentence_scores.get)
    final_summary=[word.text for word in summary]
    summary=''.join(final_summary)
    return summary

#summary of travel warnings issued by the german government
def generate_safety_report(aa_id):
    reisewarnung = requests.get("https://www.auswaertiges-amt.de/opendata/travelwarning/" + aa_id)

    #print(reisewarnung.text)

    soup = BeautifulSoup(reisewarnung.content, features="html.parser")

    CLEANR = re.compile('<.*?>')
    replace_str = "S. <em>Aktuelles</em></p><p>"

    def cleanhtml(raw_html):
        remove_notice = raw_html.replace(replace_str, "")
        cleantext = re.sub(CLEANR, ' ', remove_notice)
        return cleantext


    result = re.search('<h3>Kriminalität</h3><p>(.*?)<h2>', reisewarnung.text)
    crime = cleanhtml(result.group(1))

    original_length = len(crime.split())
    summary_percent = 50/int(original_length)
    print(summarize(crime, summary_percent))

    result = re.search('<h3>Reisedokumente</h3><p>(.*?)<strong>Anmerkungen', reisewarnung.text)
    entry_documents = cleanhtml(result.group(1))
    print(entry_documents)

    result = re.search('<h2>Natur und Klima</h2>(.*?)<h2>', reisewarnung.text)
    climate = cleanhtml(result.group(1))

    original_length = len(climate.split())
    summary_percent = 50/original_length
    print(summarize(climate, summary_percent))

    result = re.search('<h3>LGBTIQ</h3><p>(.*?)<h3>', reisewarnung.text)
    lgbtiq = cleanhtml(result.group(1))

    original_length = len(lgbtiq.split())
    summary_percent = 20/original_length
    print(summarize(lgbtiq, summary_percent))

##generate_safety_report("209524")

def create_country_safety_df():

    #read in crime rate per country from csv file and clean data
    crime_countries = pd.read_csv("../../../res/master_data/crime-rate-by-country-2023.csv")
    crime_countries_clean = crime_countries[["country", "cca3", "cca2",
                                            "crimeRateByCountry_crimeIndex"]].sort_values(by="crimeRateByCountry_crimeIndex")

    #get political stability, rule of law and personal freedom data from world bank API
    political_stability = requests.get("http://api.worldbank.org/v2/country/all/indicator/PV.EST?date=2022&per_page=500&format=json")

    rule_of_law = requests.get("http://api.worldbank.org/v2/country/all/indicator/RL.EST?date=2022&per_page=500&format=json")

    voice_and_accountability = requests.get("http://api.worldbank.org/v2/country/all/indicator/VA.EST?date=2022&per_page=500&format=json")

    #combine data into one dataframe
    safety_df = pd.DataFrame(columns=["ISO2", "ISO3", "CountryName", "PoliticalStability"])

    for i in range(len(political_stability.json()[1])):
        safety_df = pd.concat([safety_df, pd.DataFrame([{"ISO2":political_stability.json()[1][i]["country"]["id"],
                                                        "ISO3":political_stability.json()[1][i]["countryiso3code"],
                                                        "CountryName":political_stability.json()[1][i]["country"]["value"],
                                                        "PoliticalStability":political_stability.json()[1][i]["value"]}])])

    rule_of_law_df = pd.DataFrame(columns=["ISO3", "RuleofLaw"])

    for i in range(len(rule_of_law.json()[1])):
        rule_of_law_df = pd.concat([rule_of_law_df, pd.DataFrame([{"ISO3":rule_of_law.json()[1][i]["countryiso3code"],
                                                        "RuleofLaw":rule_of_law.json()[1][i]["value"]}])])

    personal_freedom_df = pd.DataFrame(columns=["ISO3", "PersonalFreedom"])

    for i in range(len(voice_and_accountability.json()[1])):
        personal_freedom_df = pd.concat([personal_freedom_df, pd.DataFrame([{
            "ISO3":voice_and_accountability.json()[1][i]["countryiso3code"],
            "PersonalFreedom":voice_and_accountability.json()[1][i]["value"]}])])

    safety_df = pd.merge(safety_df, rule_of_law_df, on="ISO3")
    safety_df = pd.merge(safety_df, personal_freedom_df, on="ISO3").sort_values(by="CountryName")
    safety_df = pd.merge(safety_df, crime_countries_clean.rename(columns={'cca3': 'ISO3'})
                        [["ISO3", "crimeRateByCountry_crimeIndex"]], on="ISO3", how="outer")

    safety_df = safety_df[safety_df['PoliticalStability'].notna()]

    #read in global peace index excel report, filter columns
    global_peace_index = pd.read_excel("../../../res/master_data/global_peace_index.xlsx", sheet_name=1, skiprows=3)
    global_peace_index = global_peace_index.rename(columns={global_peace_index.columns[17]: 'peace_index'})
    global_peace_index = global_peace_index[["Country", "iso3c", "peace_index"]]
    #read in global peace index excel report, filter columns
    global_peace_index = pd.read_excel("../../../res/master_data/global_peace_index.xlsx", sheet_name=1, skiprows=3)
    global_peace_index = global_peace_index.rename(columns={global_peace_index.columns[17]: 'peace_index'})
    global_peace_index = global_peace_index[["Country", "iso3c", "peace_index"]]

    #read in global terrorism index excel report, filter columns
    global_terrorism_index = pd.read_excel("../../../res/master_data/global_terrorism_index.xlsx", sheet_name=3, skiprows=5)
    global_terrorism_index = global_terrorism_index.rename(columns={global_terrorism_index.columns[4]: 'terrorism_index'})
    global_terrorism_index = global_terrorism_index[["Country", "iso3c", "terrorism_index"]]
    #read in global terrorism index excel report, filter columns
    global_terrorism_index = pd.read_excel("../../../res/master_data/global_terrorism_index.xlsx", sheet_name=3, skiprows=5)
    global_terrorism_index = global_terrorism_index.rename(columns={global_terrorism_index.columns[4]: 'terrorism_index'})
    global_terrorism_index = global_terrorism_index[["Country", "iso3c", "terrorism_index"]]

    #read in ecological threat excel report, filter columns
    ecological_threat_report = pd.read_excel("../../../res/master_data/ecological_threat_report.xlsx", sheet_name=1, skiprows=4)
    ecological_threat_report = ecological_threat_report.rename(columns={ecological_threat_report.columns[2]: 'ecological_threat'})
    ecological_threat_report = ecological_threat_report[["Country", "ecological_threat"]]
    #read in ecological threat excel report, filter columns
    ecological_threat_report = pd.read_excel("../../../res/master_data/ecological_threat_report.xlsx", sheet_name=1, skiprows=4)
    ecological_threat_report = ecological_threat_report.rename(columns={ecological_threat_report.columns[2]: 'ecological_threat'})
    ecological_threat_report = ecological_threat_report[["Country", "ecological_threat"]]

    #find out which countries have differing names in global peace index and ecological theat report, iso3 code is not 
    #available for ecological threat report
    no_overlap = ~global_peace_index["Country"].isin(ecological_threat_report["Country"])
    no_overlap = no_overlap.tolist()
    #print(global_peace_index.iloc[no_overlap])

    #create dict of differing country names
    country_name_dict = {"Côte d'Ivoire": "Cote d' Ivoire", "Czechia": "Czech Republic", "Gambia": "The Gambia", 
                           "Kyrgyzstan": "Kyrgyz Republic", "United States": "United States of America"}

    #replace country names
    ecological_threat_report = ecological_threat_report.replace(country_name_dict)

    #merge dataframes
    economics_and_peace_df = pd.merge(global_peace_index, global_terrorism_index[["iso3c","terrorism_index"]], on="iso3c")
    #use left join to keep Turkey, which is not present in ecological threat report
    economics_and_peace_df = pd.merge(economics_and_peace_df, ecological_threat_report, on="Country", how="left")
    safety_df = pd.merge(safety_df, economics_and_peace_df[["iso3c", "peace_index", "terrorism_index", "ecological_threat"]], 
                        left_on="ISO3", right_on="iso3c")
    safety_df = safety_df.drop("iso3c", axis=1)

    #express all metrics on a scale of 0 to 10
    scaler = MinMaxScaler((0,10))
    safety_df[['PoliticalStability', 'RuleofLaw', 'PersonalFreedom',
                'crimeRateByCountry_crimeIndex', 'peace_index',
                'terrorism_index', 'ecological_threat']] = scaler.fit_transform(
                    safety_df[['PoliticalStability', 'RuleofLaw',
                               'PersonalFreedom', 'crimeRateByCountry_crimeIndex', 'peace_index',
                               'terrorism_index', 'ecological_threat']])

    #make sure 10 is always best possible score, 0 worst possible
    safety_df[['crimeRateByCountry_crimeIndex', 'peace_index', 
               'terrorism_index', 'ecological_threat']] = 10 - safety_df[['crimeRateByCountry_crimeIndex', 
                                                                          'peace_index', 'terrorism_index', 
                                                                          'ecological_threat']]

    column_dict={"ISO2":"iso2", "ISO3":"iso3", "CountryName":"country_name", "PoliticalStability":"political_stability",
                 'RuleofLaw':"rule_of_law", 'PersonalFreedom':"personal_freedom", 'crimeRateByCountry_crimeIndex':"crime_rate"}
    safety_df.rename(columns=column_dict, inplace=True)

    return safety_df