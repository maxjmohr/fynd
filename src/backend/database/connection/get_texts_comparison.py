import os
import sys
# Add backend folder to path
parent_dir = os.path.dirname(os.path.realpath(__file__+"/../../"))
sys.path.append(parent_dir)

from database.db_helpers import Database
from datetime import datetime
from openai import OpenAI
import pandas as pd


class ComparisonPromptEngine:
    "Class to generate prompts for the GPT chatbot and return the generated comparison texts"

    def __init__(self, db:Database, model:str="gpt-3.5-turbo", temperature:float=0.8, frequency_penalty:float=0.4, max_length:int=400) -> None:
        ''' Initialize the class
        Input:  - db: the database connection
                - model: the model to be used for the chatbot
                - temperature: the temperature to be used for the chatbot
                - frequency_penalty: the frequency penalty to be used for the chatbot
                - max_length: the maximum length of the chatbot response
        Output: None
        '''
        self.db = db
        self.model = model
        self.temperature = temperature
        self.frequency_penalty = frequency_penalty
        self.max_length = max_length
        # self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_key = None
        if not self.api_key:
            current_script_directory = os.path.dirname(os.path.abspath(__file__))
            path = "../../../../res/api_keys/openai_apikey_bh.txt"
            with open(os.path.join(current_script_directory, path), "r") as f:
                self.api_key = f.read().strip()
        else:
            raise ValueError("The OpenAI API key is not set.")
        self.client = OpenAI(
            api_key=self.api_key
        )
        self.message_system = self.create_message_system()


    @staticmethod
    def create_message_system() -> dict:
        "Create the system message for the comparison text of a location category"
        return {
            "role": "system",
            "content": """You are a data interpretation system, adept at analyzing numerical variables and generating descriptive insights of travel destinations.
You are generating the text for a reader interested in traveling to the specific destination.
You are asked to generate a comparison text for a target destination based on the scores differences for each category and dimension to the previous destinations.
The scores are scaled between 0 and 1, where 0 is the worst and 1 is the best score.\n
"""
        }


    def create_message_user(self, data:dict, time_period:str, ref_start_loc:str) -> dict:
        ''' Create the user message
        Input:  - data: dictionary with previous and target location scores
                - time_period: the time period of the comparison (format: "YYYY-MM-DD to YYYY-MM-DD")
                - ref_start_loc: the reference start location of the comparison (format e.g. "Frankfurt (Germany)"
        Output: message: message to be sent to the chatbot
        '''
        # Extract some data
        previous_locs = list(data['Previous Location(s)']['Weather']['Daylight duration'].keys())
        previous_locs = " and ".join(f"'{loc}'" for loc in previous_locs)

        message = {"role": "user"}

        message["content"] = f"""Use a maximum of three paragraphs and maximum of 15 sentences to generally describe the differences in the characteristics of the target travel destination '{list(data['Target Location']['Weather']['Daylight duration'].keys())[0]} for all dimensions to the users' previous destinations {previous_locs}.
Use easy and understandable language and short sentences.
Instead of addressing 'travelers' i.e. '... safe for travelers', use 'you' or 'your' to personally address the reader.
Never generate a text containing the numeric values but rather use the distances to generate a qualitative description of the destination.
Never use the word 'score' but rather try to describe what exists more or less than in the other destinations.
The scores of all locations are for the selected time period of {time_period} and the reachability and travel costs calculated from {ref_start_loc}.
The dictionary is structured as follows: {{location type: {{category {{dimension {{location {{score}}}}}}}}}}.
{data}
Never list all dimension. Only highlight the most noteable categories and dimension standouts. Do not write an overall ending.
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
            temperature=self.temperature,
            frequency_penalty=self.frequency_penalty,
            max_length=self.max_length
        )
        return response.choices[0].message.content.strip()


    def prompt(self, data:dict, time_period:str, ref_start_loc:str) -> str:
        ''' Create prompts from the messages
        Input:  - data: dictionary with previous and target location scores
                - time_period: the time period of the comparison (format: "YYYY-MM-DD to YYYY-MM-DD")
                - ref_start_loc: the reference start location of the comparison (format e.g. "Frankfurt (Germany)"
        Output: text
        '''
        # Assert if time_period is in the right format
        if len(time_period.split(" to ")) != 2:
            raise ValueError("The time period is not in the right format. It should be 'YYYY-MM-DD to YYYY-MM-DD'.")
        
        # Extract some data
        previous_locs = list(data['Previous Location(s)']['Weather']['Daylight duration'].keys())
        previous_locs = " and ".join(f"'{loc}'" for loc in previous_locs)

        # Get comparison text
        print(f"{datetime.now()} - Generating the comparison text for '{list(data['Target Location']['Weather']['Daylight duration'].keys())[0]} and the previous locations {previous_locs}.")
        messages = [
            self.message_system,
            self.create_message_user(data, time_period, ref_start_loc)
        ]
        return self.get_response(messages)