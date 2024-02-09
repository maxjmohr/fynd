import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database
from datetime import datetime
from openai import OpenAI
import pandas as pd


class PromptEngine:
    "Class to generate prompts for the GPT chatbot and return the generated texts"

    def __init__(self, db:Database, model:str="gpt-3.5-turbo", temperature:float=0.7) -> None:
        ''' Initialize the class
        Input:  - db: the database connection
                - model: the model to be used for the chatbot
                - temperature: the temperature to be used for the chatbot
        Output: None
        '''
        self.db = db
        self.model = model
        self.temperature = temperature
        self.client = OpenAI()
        self.message_general_system = self.create_message_general_system()
        self.message_anomaly_system = self.create_message_anomaly_system()


    @staticmethod
    def create_message_general_system() -> dict:
        "Create the message for the general text of a location category"
        return {
            "role": "system",
            "content": """You are a data interpretation system, adept at analyzing numerical variables and generating descriptive insights of travel destinations.
You are generating the text for a reader interested in traveling to the specific destination. Use easy and understandable language and short sentences.
Instead of addressing 'travelers' i.e. '... safe for travelers', use 'you' or 'your' to personally address the reader.
You are asked to generate a general text for a destination category based on the distances to the median of the dimensions.
A positive distance indicates that the destination is above the median, while a negative distance indicates that the destination is below the median.
Lower i.e. negative values correlate with a worse respective score in the category, while higher i.e. positive values correlate with a better respective score in the category.
Larger distances indicate a larger deviation from the median. Larger distances should be highlighted more in the generated text than smaller ones.
Try to phrase a key message for the destination in this category, weighing all dimensions equally. Avoid generic phrases and rather focus on the specific destination.
Never generate a text containing the numeric values but rather use the distances to generate a qualitative description of the destination.
Do not use the word 'median' too often but try to exchange it with logical synonyms (e.g. 'compared to other destinations').\n
"""
        }


    @staticmethod
    def create_message_anomaly_system() -> dict:
        "Create the message for the anomaly text of a location category"
        return {
            "role": "system",
            "content": """You are a data interpretation system, adept at analyzing numerical variables and generating descriptive insights of travel destinations based on detected anomalies.
You are generating the text for a reader interested in traveling to the specific destination. Use easy and understandable language and short sentences.
Instead of addressing 'travelers' i.e. '... safe for travelers', use 'you' or 'your' to personally address the reader.
You are asked to generate an anomaly text for a destination category based on the distances to the anomaly bounds (highest or lowest 10%) of the dimensions.
All displayed values are anomalies. Integrate all anomalies into the core message of the anomaly text and especially highlight those that are most significant.
A positive distance indicates that the destination is above the upper bound, while a negative distance indicates that the destination is below the lower bound.
Lower i.e. negative values correlate with a worse respective score in the category, while higher i.e. positive values correlate with a better respective score in the category.
Larger distances indicate a larger deviation from the bounds (i.e. a stronger anomaly). Stronger anomalies should be highlighted more in the generated text than weaker ones.
You will be given a general text (where every dimension should already be generally described) that you should use as a basis for generating the anomaly text.
Analyze the key message of the general text and further intensify the message by now more noteably highlighting the anomalies.
Do not repeat any messages from the general text but rather add new information in terms of anomalies. Rather generate less sentences than repeat the same information.
Do not start the anomaly text with a sentence that describes the core message of the general text. Avoid generic phrases and rather focus on the specific destination.
The transition should be seemless and try to use different wording than in the general text. Only output the newly generated text (not the general text).
Never generate a text containing the numeric values but rather use the distances to generate a qualitative description of the destination.
Do not use the word 'bound' too often but try to exchange it with logical synonyms (e.g. 'compared to other destinations').\n
"""
        }


    @staticmethod
    def content_seasonal_distances(data:pd.DataFrame, which_distance:str) -> str:
        ''' Get the content part of the seasonal distances
        Input:  - data: the data along with category and dimension id
                - which_distance: the distance to be used for the content
        Output: formatted_content: the formatted content for the seasonal distances
        '''
        # Assert that there is only one unique category_id
        assert data["category_id"].nunique() == 1, "The category_id is not unique."

        # Get distance metric string
        distance_metric = which_distance.replace("distance_to_", "")

        # Order data by start_date and dimension_id
        data = data.sort_values(by=["start_date", "dimension_id"], ascending=True)

        # Initialize an empty string to store the formatted content
        formatted_content = f"""Take into account the seasonal differences in the distances to the {distance_metric}s of the dimensions.
The following table shows the distances to the {distance_metric}s for the corresponding dimensions and time periods:\n
"""

        # Iterate through each time period
        for start_date in (data["start_date"].unique()):

            # Get the data for the specific start_date
            data_start_date = data[data["start_date"] == start_date]

            # Format the start_date
            formatted_content += f"* Time period: {start_date} - {data_start_date['end_date'].unique()[0]}\n"

            # Format the dimension name and distance
            dimension_distance_pairs = ""
            for dimension_name, distance in zip(data_start_date['dimension_name'], data_start_date[which_distance]):
                dimension_distance_pairs += f"  * {dimension_name}: {distance}\n"

            # Add the dimension name and distance to the formatted content
            formatted_content += dimension_distance_pairs

        return formatted_content


    @staticmethod
    def content_non_seasonal_distances(data:pd.DataFrame, which_distance:str) -> str:
        ''' Get the content part of the non-seasonal distances
        Input:  - data: the data along with category and dimension id
                - which_distance: the distance to be used for the content
        Output: formatted_content: the formatted content for the non-seasonal distances
        '''
        # Assert that there is only one unique category_id
        assert data["category_id"].nunique() == 1, "The category_id is not unique."

        # Get distance metric string
        distance_metric = which_distance.replace("distance_to_", "")

        # Order data by dimension_id
        data = data.sort_values(by="dimension_id", ascending=True)

        # Initialize an empty string to store the formatted content
        formatted_content = f"""Take into account the differences in the distances to the {distance_metric}s of the dimensions.
The following table shows the distances to the {distance_metric}s for the corresponding dimensions:\n
"""
        
        # Format the dimension name and distance
        dimension_distance_pairs = ""
        for dimension_name, distance in zip(data['dimension_name'], data[which_distance]):
            dimension_distance_pairs += f"* {dimension_name}: {distance}\n"

        # Add the dimension name and distance to the formatted content
        formatted_content += dimension_distance_pairs

        return formatted_content


    def create_message_general_user(self, data:pd.DataFrame) -> dict:
        ''' Create the message for the user
        Input:  data: the data along with category and dimension id
        Output: message: message to be sent to the chatbot
        '''
        # Assert that there is only one unique category_id
        assert data["category_id"].nunique() == 1, "The category_id is not unique."

        message = {"role": "user"}

        # For weather, reachability
        if 2 in data["category_id"].unique() or 6 in data["category_id"].unique():

            message["content"] = f"""Use a maximum of five sentences in the paragraph to generally describe the characteristics of the travel destination {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) for the dimensions of the category '{data['category_name'].iloc[0]}'.
{self.content_seasonal_distances(data, "distance_to_median")}
"""

        # For costs, especially for travel/accommodation costs
        elif 4 in data["category_id"].unique():

            message["content"] = f"""Use a maximum of five sentences in the paragraph to generally describe the characteristics of the travel destination {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) for the dimensions of the category '{data['category_name'].iloc[0]}'.
{self.content_non_seasonal_distances(data[~data['dimension_id'].isin([41, 42])], "distance_to_median")}
{self.content_seasonal_distances(data[data['dimension_id'].isin([41, 42])], "distance_to_median")}
"""

        else:

            message["content"] = f"""Use a maximum of five sentences in the paragraph to generally describe the characteristics of the travel destination {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) for the dimensions of the category '{data['category_name'].iloc[0]}'.
{self.content_non_seasonal_distances(data, "distance_to_median")}
"""
        return message


    def create_message_anomaly_user(self, data:pd.DataFrame, text_general:str) -> dict:
        ''' Create the message for the user
        Input:  - data: the data along with category and dimension id
                - text_general: generated general text for context
        Output: message: message to be sent to the chatbot
        '''

        # Assert that there is only one unique category_id
        assert data["category_id"].nunique() == 1, "The category_id is not unique."

        message = {"role": "user"}

        # For testing: Drop null values in column distance_to_bound
        data = data[data["distance_to_bound"].notnull()]

        # For weather, reachability and travel/accommodation costs
        if 2 in data["category_id"].unique() or 6 in data["category_id"].unique():

            message["content"] = f"""Use a maximum of five sentences in the paragraph to highlight the anomalies of the travel destination {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) for the dimensions of the category '{data['category_name'].iloc[0]}'.
{self.content_seasonal_distances(data, "distance_to_bound")}
Generate the anomaly text in a way that it is consistent with the general text and fits right after the general text.
Only output the newly generated text (not the general text).\n
General text: '''
{text_general}
'''
"""

        # For costs, especially for travel/accommodation costs
        elif 4 in data["category_id"].unique():

            message["content"] = f"""Use a maximum of five sentences in the paragraph to highlight the anomalies of the travel destination {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) for the dimensions of the category '{data['category_name'].iloc[0]}'.
{self.content_non_seasonal_distances(data[~data['dimension_id'].isin([41, 42])], "distance_to_bound")}
{self.content_seasonal_distances(data[data['dimension_id'].isin([41, 42])], "distance_to_bound")}
Generate the anomaly text in a way that it is consistent with the general text and fits right after the general text.
Only output the newly generated text (not the general text).\n
General text: '''
{text_general}
'''
"""

        else:

            message["content"] = f"""Use a maximum of five sentences in the paragraph to highlight the anomalies of the travel destination {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) for the dimensions of the category '{data['category_name'].iloc[0]}'.
{self.content_non_seasonal_distances(data, "distance_to_bound")}
Generate the anomaly text in a way that fits right after the general text. The transition should be seemless and try to use different wording than in the general text.
Only output the newly generated text (not the general text).\n
General text: '''
{text_general}
'''
"""
        return message


    def get_response(self, messages:list) -> str:
        ''' Get the response of the chatbot
        Input:  message: the message to be sent to the chatbot
        Output: response: the response of the chatbot
        '''
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        return response.choices[0].message


    def prompt(self, data:pd.DataFrame) -> pd.DataFrame:
        ''' Create prompts from the messages
        Input:  data: the data along with category and dimension id
        Output: df: the resulting dataframe with the general and anomaly texts
        '''
        # Initiate resulting dataframe
        df = pd.DataFrame({
            "location_id": [data["location_id"].iloc[0]],
            "category_id": [data["category_id"].iloc[0]],
            "ref_start_location_id": [data["ref_start_location_id"].iloc[0]],
        })

        # Get general text
        print(f"{datetime.now()} - Generating the general text for '{data['location_city'].iloc[0]} ({data['location_country'].iloc[0]})', category '{data['category_id'].iloc[0]}', start location '{data['start_location_city'].iloc[0]} ({data['start_location_country'].iloc[0]})'.")
        messages = [
            self.message_general_system,
            self.create_message_general_user(data)
        ]
        df["text_general"] = self.get_response(messages)

        # Reachability extra sentence
        if data["category_id"].iloc[0] == 6:
            assert data["ref_start_location_id"] != -1, "There is no reference start location related to the reachability scores."

            df["text_general"] = f"""To calculate the reachability, we use a fixed selection of reference start locations.
Based on your selected start location, the reference start location is {data['start_location_city'].iloc[0]} ({data['start_location_country'].iloc[0]}).\n
{df['text_general'].iloc[0]}
"""

        # Get anomaly text (if there are anomalies detected)
        if data["distance_to_bound"].isnull().all():
            print(f"{datetime.now()} - No anomalies for '{data['location_name'].iloc[0]}v, category '{data['category_id'].iloc[0]}', start location '{data['start_location_name'].iloc[0]}'.")
            df["text_anomaly"] = None

        else:
            print(f"{datetime.now()} - Generating the anomaly text for '{data['location_name'].iloc[0]}', category '{data['category_id'].iloc[0]}', start location '{data['start_location_name'].iloc[0]}'.")
            messages = [
                self.message_anomaly_system,
                self.create_message_anomaly_user(data[data["distance_to_bound"].notnull()], df["text_general"])
            ]
            df["text_anomaly"]  = self.get_response(messages)

        # Add start_date and end_date
        df["start_date"] = datetime(2023, 1, 1).date()
        df["end_date"] = datetime(2099, 12, 31).date()

        # Restructure data and insert into db
        df = df[["location_id", "category_id", "start_date", "end_date", "ref_start_location_id", "text_general", "text_anomaly"]]
        self.db.insert_data(texts, "core_texts")

        return df


def prepare_text_generation(db:Database, filter_cats:list) -> pd.DataFrame:
    ''' Preprocess the data from core_scores into the batches for the text generation
    Input:  - db: the database connection
            - filter_cats: the categories to be filtered
    Output: data: the preprocessed data
    '''
    # Load data
    scores = db.fetch_data("core_scores")
    loaded_texts = db.fetch_data("core_texts")
    locations = db.fetch_data("core_locations")
    start_locations = db.fetch_data("core_ref_start_locations")
    categories = db.fetch_data("core_categories")

    # Filter categories
    if filter_cats:
        scores = scores[scores["category_id"].isin(filter_cats)]

    # If categories include 3 (culture), get scores and distances from other table and append
    if 3 in filter_cats:
        # Delete the scores from the main table+
        scores = scores[scores["category_id"] != 3]

        # Get scores and distances from the culture table
        scores_culture = db.fetch_data("core_scores_culture")
        scores_culture = scores_culture[scores_culture["category_id"] == 3]
        scores = pd.concat([scores, scores_culture], ignore_index=True)

    scores = scores.groupby(["location_id", "category_id", "ref_start_location_id"])

    # Check whether texts for groups were already generated
    scores = scores.filter(lambda x: x.name not in loaded_texts[["location_id", "category_id", "ref_start_location_id"]])
    scores = scores.reset_index(drop=True)

    # Join the names of the locations and start_locations and categories
    scores = scores.merge(
        locations[["location_id", "city", "country"]],
        on="location_id", how="inner"
        )
    scores.rename(columns={"city": "location_city", "country": "location_country"}, inplace=True)

    scores = scores.merge(
        start_locations[["ref_start_location_id", "city", "country"]],
        left_on="location_id", right_on="ref_start_location_id", how="left"
        )
    scores.rename(columns={"city": "start_location_city", "country": "start_location_country"}, inplace=True)

    scores = scores.merge(
        categories[["category_id", "category_name"]],
        on="category_id", how="inner"
        )

    return scores


if __name__ == "__main__":
    # Connect to database
    db = Database()
    db.connect()

    # Get data
    filter_cats = [
        #0, # General
        #1, # Safety
        #2, # Weather
        #3, # Culture
        #4, # Cost
        #5, # Geography
        #6, # Reachability
        #7 # Health
    ]
    data = prepare_text_generation(db, filter_cats)

    # Generate texts
    prompt_engine = PromptEngine(db)
    texts = data.apply(prompt_engine.prompt, axis=1)

    # Disconnect from database
    db.disconnect()