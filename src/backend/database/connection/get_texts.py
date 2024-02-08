import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database
from openai import OpenAI
import pandas as pd


class PromptEngine:
    "Class to generate prompts for the GPT chatbot and return the generated texts"

    def __init__(self, model:str="gpt-3.5-turbo", temperature:float=0.) -> None:
        ''' Initialize the class
        Input:  - model: the model to be used for the chatbot
                - temperature: the temperature to be used for the chatbot
        Output: None
        '''
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
            "content": "You are a data interpretation system, adept at analyzing numerical variables and generating descriptive insights."
        }


    @staticmethod
    def create_message_anomaly_system() -> dict:
        "Create the message for the anomaly text of a location category"
        return {
            "role": "system",
            "content": "You are a data interpretation system, adept at analyzing numerical variables and generating descriptive insights based on detected anomalies."
        }


    @staticmethod
    def content_seasonal_distances(distances:pd.DataFrame, which_distance:str) -> str:
        ''' Get the content part of the seasonal distances
        Input:  - distances: the distances along with category and dimension id
                - which_distance: the distance to be used for the content
        Output: formatted_content: the formatted content for the seasonal distances
        '''
        # Assert that there is only one unique category_id
        assert distances["category_id"].nunique() == 1, "The category_id is not unique."

        # Get distance metric string
        distance_metric = which_distance.replace("distance_to_", "")

        # Order distances by start_date and dimension_id
        distances = distances.sort_values(by=["start_date", "dimension_id"], ascending=True)

        # Initialize an empty string to store the formatted content
        formatted_content = f"""
Take into account the seasonal differences in the distances to the {distance_metric}s of the dimensions.\n
The following table shows the distances to the {distance_metric}s for the corresponding dimensions and time periods:\n
"""

        # Iterate through each row of the DataFrame
        for _, row in distances.iterrows():
            # Format the time period
            time_period = f"* Time period: {row['start_date']} - {row['end_date']}\n"
            formatted_content += time_period
            
            # Format the dimension name and distance
            dimension_distance_pairs = ""
            for dimension_name, distance in zip(row['dimension_name'], row[which_distance]):
                dimension_distance_pairs += f"  * {dimension_name}: {distance}\n"
            
            # Add the dimension name and distance to the formatted content
            formatted_content += dimension_distance_pairs

        return formatted_content


    @staticmethod
    def content_non_seasonal_distances(distances:pd.DataFrame, which_distance:str) -> str:
        ''' Get the content part of the non-seasonal distances
        Input:  - distances: the distances along with category and dimension id
                - which_distance: the distance to be used for the content
        Output: formatted_content: the formatted content for the non-seasonal distances
        '''
        # Get distance metric string
        distance_metric = which_distance.replace("distance_to_", "")

        # Order distances by dimension_id
        distances = distances.sort_values(by="dimension_id", ascending=True)

        # Initialize an empty string to store the formatted content
        formatted_content = f"""
Take into account the differences in the distances to the {distance_metric}s of the dimensions.\n
The following table shows the distances to the {distance_metric}s for the corresponding dimensions:\n
"""
        
        # Format the dimension name and distance
        dimension_distance_pairs = ""
        for dimension_name, distance in zip(distances['dimension_name'], distances[which_distance]):
            dimension_distance_pairs += f"* {dimension_name}: {distance}\n"

        # Add the dimension name and distance to the formatted content
        formatted_content += dimension_distance_pairs

        return formatted_content


    def create_message_general_user(self, distances:pd.DataFrame) -> dict:
        ''' Create the message for the user
        Input:  distances: the distances along with category and dimension id
        Output: message: message to be sent to the chatbot
        '''
        # Assert that there is only one unique category_id
        assert distances["category_id"].nunique() == 1, "The category_id is not unique."

        message = {"role": "user"}

        # For weather, reachability and travel/accommodation costs
        if distances["category_id"].any() in [2, 6] or distances["dimension_id"].any() in [41, 42]:

            message["content"] = f"""
Use a maximum of five sentences in the paragraph to generally describe the characteristics of the location for the following dimensions of this category:
{self.content_seasonal_distances(distances, "distance_to_median")}
"""

        else:

            message["content"] = f"""
Use a maximum of five sentences in the paragraph to generally describe the characteristics of the location for the following dimensions of this category:
{self.content_non_seasonal_distances(distances, "distance_to_median")}
"""
        return message


    def create_message_anomaly_user(self, distances:pd.DataFrame, text_general:str) -> dict:
        ''' Create the message for the user
        Input:  - distances: the distances along with category and dimension id
                - text_general: generated general text for context
        Output: message: message to be sent to the chatbot
        '''

        # Assert that there is only one unique category_id
        assert distances["category_id"].nunique() == 1, "The category_id is not unique."

        message = {"role": "user"}

        # For weather, reachability and travel/accommodation costs
        if distances["category_id"].any() in [2, 6] or distances["dimension_id"].any() in [41, 42]:

            message["content"] = f"""
Use a maximum of five sentences in the paragraph to describe the anomalies of the location for the dimensions of the category '{distances['category_name']}'.\n
{self.content_seasonal_distances(distances, "distance_to_bound")}
Generate the anomaly text in a way that it is consistent with the general text and fits right after the general text.\n
Text: '''\n
{text_general}\n
'''
"""

        else:

            message["content"] = f"""
Use a maximum of five sentences in the paragraph to describe the anomalies of the location for the dimensions of the category '{distances['category_name']}'.\n
{self.content_non_seasonal_distances(distances, "distance_to_bound")}
Generate the anomaly text in a way that it is consistent with the general text and fits right after the general text.\n
Text: '''\n
{text_general}\n
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
            messages=messages
        )
        return response.choices[0].message


    def prompt(self, distances:pd.DataFrame) -> list:
        ''' Create prompts from the messages
        Input:  distances: the distances along with category and dimension id
        Output: prompt: prompt as messages to be sent to the chatbot
        '''
        # Get general text
        messages = [
            self.message_general_system,
            self.create_message_general_user(distances)
        ]
        text_general = self.get_response(messages)

        # Get anomaly text
        messages = [
            self.message_anomaly_system,
            self.create_message_anomaly_user(distances, text_general)
        ]
        text_anomaly = self.get_response(messages)

        return [text_general, text_anomaly]