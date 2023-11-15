#https://developer.tugo.com/docs/read/travelsafe/v1/country

import requests
from bs4 import BeautifulSoup
import re
from amadeus import Client, ResponseError
# import client, secret key stored in separate file
from amadeus_key import client_id, client_secret

import spacy
from spacy.lang.de.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest

import json
import pandas as pd

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

#teleport api
def get_teleport_city_safety(city):
    api_string = "https://api.teleport.org/api/urban_areas/slug:" + city + "/scores/"
    city_safety = requests.get(api_string)

    teleport_safety_df = pd.DataFrame.from_dict(city_safety.json()["categories"])

    teleport_safety_df = teleport_safety_df.drop(columns=["color"])
    teleport_safety_df = teleport_safety_df.rename(columns={"name":"Category", "score_out_of_10":"ScoreOutOf10"})

    print(teleport_safety_df)

get_teleport_city_safety("berlin")

#travel advisory --> scores inacurate
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

generate_safety_report("209524")

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

print(safety_df[safety_df["ISO3"]=="CAN"])
