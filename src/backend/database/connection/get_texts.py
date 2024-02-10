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

    def __init__(self, db:Database, model:str="gpt-3.5-turbo", temperature:float=0.9, frequency_penalty:float=0.35) -> None:
        ''' Initialize the class
        Input:  - db: the database connection
                - model: the model to be used for the chatbot
                - temperature: the temperature to be used for the chatbot
        Output: None
        '''
        self.db = db
        self.model = model
        self.temperature = temperature
        self.frequency_penalty = frequency_penalty
        # self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_key = None
        if not self.api_key:
            current_script_directory = os.path.dirname(os.path.abspath(__file__))
            path = "../../../../res/api_keys/openai_apikey_fk.txt"
            with open(os.path.join(current_script_directory, path), "r") as f:
                self.api_key = f.read().strip()
        else:
            raise ValueError("The OpenAI API key is not set.")
        self.client = OpenAI(
            api_key=self.api_key
        )
        self.message_general_system = self.create_message_general_system()
        self.message_anomaly_system = self.create_message_anomaly_system()


    @staticmethod
    def create_message_general_system() -> dict:
        "Create the message for the general text of a location category"
        return {
            "role": "system",
            "content": """You are a data interpretation system, adept at analyzing numerical variables and generating descriptive insights of travel destinations.
You are generating the text for a reader interested in traveling to the specific destination.
You are asked to generate a general text for a destination category based on the distances to the median of the dimensions.
A positive distance indicates that the destination is above the median, while a negative distance indicates that the destination is below the median.
Lower i.e. negative values correlate with a worse respective score in the category, while higher i.e. positive values correlate with a better respective score in the category.
Larger distances indicate a larger deviation from the median. Larger distances should be highlighted more in the generated text than smaller ones.\n
"""
        }


    @staticmethod
    def create_message_anomaly_system() -> dict:
        "Create the message for the anomaly text of a location category"
        return {
            "role": "system",
            "content": """You are a data interpretation system, adept at analyzing numerical variables and generating descriptive insights of travel destinations based on detected anomalies.
You are generating the text for a reader interested in traveling to the specific destination.
You are asked to generate an anomaly text for a destination category based on the distances to the anomaly bounds (highest or lowest 10%) of the dimensions.
A positive distance indicates that the destination is above the upper bound, while a negative distance indicates that the destination is below the lower bound.
Lower i.e. negative values correlate with a worse respective score in the category, while higher i.e. positive values correlate with a better respective score in the category.
Larger distances indicate a larger deviation from the bounds (i.e. a stronger anomaly). Stronger anomalies should be highlighted more in the generated text than weaker ones.\n
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
        formatted_content = f""""Do not use the word '{distance_metric}' but try to exchange it with logical synonyms (e.g. 'compared to other destinations').
Especially compare {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) to seosonal trends of other destinations in the category '{data['category_name'].iloc[0]}'.
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

        # Add last sentence
        formatted_content += f"Take into account the seasonal differences in the distances to the {distance_metric}s of the dimensions to phrase a key message for the destination in this category. Avoid generic phrases and rather focus on the specific destination.\n"

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
        formatted_content = f"""Do not use the word '{distance_metric}' but try to exchange it with logical synonyms (e.g. 'compared to other destinations').
The following table shows the distances to the {distance_metric}s for the corresponding dimensions:\n
"""
        
        # Format the dimension name and distance
        dimension_distance_pairs = ""
        for dimension_name, distance in zip(data['dimension_name'], data[which_distance]):
            dimension_distance_pairs += f"* {dimension_name}: {distance}\n"

        # Add the dimension name and distance to the formatted content
        formatted_content += dimension_distance_pairs

        # Add last sentence
        formatted_content += f"Take into account the differences in the distances to the {distance_metric}s of the dimensions to phrase the key messages in this category. Avoid generic phrases and rather focus on the specific destination.\n"

        return formatted_content


    def create_message_general_user(self, data:pd.DataFrame) -> dict:
        ''' Create the message for the user
        Input:  data: the data along with category and dimension id
        Output: message: message to be sent to the chatbot
        '''
        # Assert that there is only one unique category_id
        assert data["category_id"].nunique() == 1, "The category_id is not unique."

        message = {"role": "user"}

        # For weather and reachability
        if 2 in data["category_id"].unique() or 6 in data["category_id"].unique():

            message["content"] = f"""Use a maximum of one paragraph to generally describe the characteristics of the travel destination {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) for the dimensions of the category '{data['category_name'].iloc[0]}'.
Use easy and understandable language and short sentences.
Instead of addressing 'travelers' i.e. '... safe for travelers', use 'you' or 'your' to personally address the reader.
Especially compare {data['location_city'].iloc[0]} to other destinations in the category '{data['category_name'].iloc[0]}'.
Never generate a text containing the numeric values but rather use the distances to generate a qualitative description of the destination.
{self.content_seasonal_distances(data, "distance_to_median")} 
"""

        # For costs, especially for travel/accommodation costs
        elif 4 in data["category_id"].unique():

            message["content"] = f"""Use a maximum of one paragraph to generally describe the characteristics of the travel destination {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) for the dimensions of the category '{data['category_name'].iloc[0]}'.
Use easy and understandable language and short sentences.
Instead of addressing 'travelers' i.e. '... safe for travelers', use 'you' or 'your' to personally address the reader.
Especially compare {data['location_city'].iloc[0]} to other destinations in the category '{data['category_name'].iloc[0]}'.
Never generate a text containing the numeric values but rather use the distances to generate a qualitative description of the destination.
{self.content_non_seasonal_distances(data[~data['dimension_id'].isin([41, 42])], "distance_to_median")}
{self.content_seasonal_distances(data[data['dimension_id'].isin([41, 42])], "distance_to_median")}
"""

        else:

            message["content"] = f"""Use a maximum of one paragraph to generally describe the characteristics of the travel destination {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) for the dimensions of the category '{data['category_name'].iloc[0]}'.
Use easy and understandable language and short sentences.
Instead of addressing 'travelers' i.e. '... safe for travelers', use 'you' or 'your' to personally address the reader.
Especially compare {data['location_city'].iloc[0]} to other destinations in the category '{data['category_name'].iloc[0]}'.
Never generate a text containing the numeric values but rather use the distances to generate a qualitative description of the destination.
{self.content_non_seasonal_distances(data, "distance_to_median")}
"""
        return message


    def create_message_anomaly_user(self, data:pd.DataFrame) -> dict:
        ''' Create the message for the user
        Input:  data: the data along with category and dimension id
        Output: message: message to be sent to the chatbot
        '''

        # Assert that there is only one unique category_id
        assert data["category_id"].nunique() == 1, "The category_id is not unique."

        message = {"role": "user"}

        # For testing: Drop null values in column distance_to_bound
        data = data[data["distance_to_bound"].notnull()]

        # For weather and reachability
        if 2 in data["category_id"].unique() or 6 in data["category_id"].unique():

            message["content"] = f"""Use a maximum of five sentences in the paragraph to highlight the anomalies of the travel destination {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) for the dimensions of the category '{data['category_name'].iloc[0]}'.
Use easy and understandable language and short sentences.
Instead of addressing 'travelers' i.e. '... safe for travelers', use 'you' or 'your' to personally address the reader.
Especially compare {data['location_city'].iloc[0]} to other destinations in the category '{data['category_name'].iloc[0]}'.
Never generate a text containing the numeric values but rather use the distances to generate a qualitative description of the destination.
Never describe the actual distance to a bound and never describe the bound but rather highlight that this dimension is a positive/negative anomoly.
{self.content_seasonal_distances(data, "distance_to_bound")}
All listed dimensions are the anomalies, NOT THE DISTANCES TO AVERAGE BUT TO THE BOUNDS.
Don't describe positive or negative anomalies but rather "increased/decreased" or "stronger/weaker" or others.
Generate the first sentence as a transition from the general paragraph regarding '{data['category_name'].iloc[0]}' into now the more special anomalies of the same category (such as "Looking at .. in more depth,...", "Furthermore,...", "More specifically,..." and others).\n
"""

        # For costs, especially for travel/accommodation costs
        elif 4 in data["category_id"].unique():

            message["content"] = f"""Use a maximum of five sentences in the paragraph to highlight the anomalies of the travel destination {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) for the dimensions of the category '{data['category_name'].iloc[0]}'.
Use easy and understandable language and short sentences.
Instead of addressing 'travelers' i.e. '... safe for travelers', use 'you' or 'your' to personally address the reader.
Especially compare {data['location_city'].iloc[0]} to other destinations in the category '{data['category_name'].iloc[0]}'.
Never generate a text containing the numeric values but rather use the distances to generate a qualitative description of the destination.
Never describe the actual distance to a bound and never describe the bound but rather highlight that this dimension is a positive/negative anomoly.
{self.content_non_seasonal_distances(data[~data['dimension_id'].isin([41, 42])], "distance_to_bound")}
{self.content_seasonal_distances(data[data['dimension_id'].isin([41, 42])], "distance_to_bound")}
All listed dimensions are the anomalies, NOT THE DISTANCES TO AVERAGE BUT TO THE BOUNDS.
Don't describe positive or negative anomalies but rather "increased/decreased" or "stronger/weaker" or others.
Generate the first sentence as a transition from the general paragraph regarding '{data['category_name'].iloc[0]}' into now the more special anomalies of the same category (such as "Looking at .. in more depth,...", "Furthermore,...", "More specifically,..." and others).\n
"""

        else:

            message["content"] = f"""Use a maximum of five sentences in the paragraph to highlight the anomalies of the travel destination {data['location_city'].iloc[0]} ({data['location_country'].iloc[0]}) for the dimensions of the category '{data['category_name'].iloc[0]}'.
Use easy and understandable language and short sentences.
Instead of addressing 'travelers' i.e. '... safe for travelers', use 'you' or 'your' to personally address the reader.
Especially compare {data['location_city'].iloc[0]} to other destinations in the category '{data['category_name'].iloc[0]}'.
Never generate a text containing the numeric values but rather use the distances to generate a qualitative description of the destination.
Never describe the actual distance to a bound and never describe the bound but rather highlight that this dimension is a positive/negative anomoly.
{self.content_non_seasonal_distances(data, "distance_to_bound")}
All listed dimensions are the anomalies, NOT THE DISTANCES TO AVERAGE BUT TO THE BOUNDS.
Don't describe positive or negative anomalies but rather "increased/decreased" or "stronger/weaker" or others.
Generate the first sentence as a transition from the general paragraph regarding '{data['category_name'].iloc[0]}' into now the more special anomalies of the same category (such as "Looking at .. in more depth,...", "Furthermore,...", "More specifically,..." and others).\n
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
            frequency_penalty=self.frequency_penalty
        )
        return response.choices[0].message.content.strip()


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
        print(f"{datetime.now()} - Generating the general text for '{data['location_city'].iloc[0]} ({data['location_country'].iloc[0]})', category '{data['category_name'].iloc[0]}', start location '{data['start_location_city'].iloc[0]} ({data['start_location_country'].iloc[0]})'.")
        messages = [
            self.message_general_system,
            self.create_message_general_user(data)
        ]
        df["text_general"] = self.get_response(messages)

        # Reachability extra sentence
        if data["category_id"].iloc[0] == 6:
            assert data["ref_start_location_id"].iloc[0] != -1, "There is no reference start location related to the reachability scores."

            df["text_general"] = f"""To calculate the reachability, we use a fixed selection of reference start locations.
Based on your selected start location, the reference start location is {data['start_location_city'].iloc[0]} ({data['start_location_country'].iloc[0]}).\n
{df['text_general'].iloc[0]}
"""

        # Get anomaly text (if there are anomalies detected)
        if data["distance_to_bound"].isnull().all():
            print(f"{datetime.now()} - No anomalies for '{data['location_city'].iloc[0]} ({data['location_country'].iloc[0]})', category '{data['category_name'].iloc[0]}', start location '{data['start_location_city'].iloc[0]} ({data['start_location_country'].iloc[0]})'.")
            df["text_anomaly"] = None

        else:
            print(f"{datetime.now()} - Generating the anomaly text for '{data['location_city'].iloc[0]} ({data['location_country'].iloc[0]})', category '{data['category_name'].iloc[0]}', start location '{data['start_location_city'].iloc[0]} ({data['start_location_country'].iloc[0]})'.")
            messages = [
                self.message_anomaly_system,
                self.create_message_anomaly_user(data[data["distance_to_bound"].notnull()])
            ]
            df["text_anomaly"]  = self.get_response(messages)

        # Add start_date and end_date
        df["start_date"] = datetime(2023, 1, 1).date()
        df["end_date"] = datetime(2099, 12, 31).date()

        # Restructure data and insert into db
        df = df[["location_id", "category_id", "start_date", "end_date", "ref_start_location_id", "text_general", "text_anomaly"]]
        self.db.insert_data(df, "core_texts")

        return df


def prepare_text_generation(db:Database, filter_cats:list, testing:bool) -> pd.DataFrame:
    ''' Preprocess the data from core_scores into the batches for the text generation
    Input:  - db: the database connection
            - filter_cats: the categories to be filtered
            - testing: whether the function is used for testing
    Output: data: the preprocessed data
    '''
    sql = f"""
    WITH
        grouped_scores AS (
            SELECT
                s.location_id,
                s.category_id,
                s.ref_start_location_id
            FROM
                core_scores s
            WHERE
                s.category_id IN ({", ".join([str(cat) for cat in filter_cats])})
            GROUP BY
                s.location_id,
                s.category_id,
                s.ref_start_location_id
        ),

        loaded_texts AS (
            SELECT
                t.location_id,
                t.category_id,
                t.ref_start_location_id
            FROM
                core_texts t
            GROUP BY
                t.location_id,
                t.category_id,
                t.ref_start_location_id
        ),

        not_loaded_scores AS (
            SELECT
                s.location_id,
                s.category_id,
                s.ref_start_location_id
            FROM
                grouped_scores s
            WHERE
                (s.location_id, s.category_id, s.ref_start_location_id) NOT IN (
                    SELECT
                        t.location_id,
                        t.category_id,
                        t.ref_start_location_id
                    FROM
                        loaded_texts t
                )
        ),

        not_loaded_scores_with_info AS (
            SELECT
                s.location_id,
                l.city AS location_city,
                l.country AS location_country,
                s.category_id,
                c.category_name,
                s.dimension_id,
                d.dimension_name,
                s.start_date,
                s.end_date,
                s.ref_start_location_id,
                r.city AS start_location_city,
                r.country AS start_location_country,
                CAST(s.score AS DOUBLE PRECISION) AS score,
                CAST(s.raw_value AS DOUBLE PRECISION) AS raw_value,
                CAST(s.distance_to_median AS DOUBLE PRECISION) AS distance_to_median,
                CAST(s.distance_to_bound AS DOUBLE PRECISION) AS distance_to_bound
            FROM
                core_scores s
                INNER JOIN not_loaded_scores n ON s.location_id = n.location_id AND s.category_id = n.category_id AND s.ref_start_location_id = n.ref_start_location_id
                INNER JOIN core_locations l ON l.location_id = s.location_id
                INNER JOIN core_categories c ON c.category_id = s.category_id
                INNER JOIN core_dimensions d ON d.dimension_id = s.dimension_id
                LEFT JOIN core_ref_start_locations r ON s.ref_start_location_id = r.location_id
            WHERE
                {"" if not testing else "l.city = 'Munich' AND l.country = 'Germany'"}
                AND (s.category_id != 2 OR (s.category_id = 2 AND EXTRACT(YEAR FROM s.start_date) = 2024))
        ),


        not_loaded_scores_culture AS (
            SELECT
                s.location_id,
                l.city AS location_city,
                l.country AS location_country,
                s.category_id,
                c.category_name,
                s.dimension_id,
                s.dimension_name,
                s.start_date,
                s.end_date,
                s.ref_start_location_id,
                r.city AS start_location_city,
                r.country AS start_location_country,
                CAST(s.score AS DOUBLE PRECISION) AS score,
                CAST(s.raw_value AS DOUBLE PRECISION) AS raw_value,
                CAST(s.distance_to_median AS DOUBLE PRECISION) AS distance_to_median,
                CAST(s.distance_to_bound AS DOUBLE PRECISION) AS distance_to_bound
            FROM
                raw_subscores_culture s
                INNER JOIN not_loaded_scores n ON s.location_id = n.location_id AND s.category_id = n.category_id AND s.ref_start_location_id = n.ref_start_location_id
                INNER JOIN core_locations l ON l.location_id = s.location_id
                INNER JOIN core_categories c ON c.category_id = s.category_id
                LEFT JOIN core_ref_start_locations r ON s.ref_start_location_id = r.location_id
            WHERE
                {"" if not testing else "l.city = 'Munich' AND l.country = 'Germany'"}
        )

    SELECT
        *
    FROM
        not_loaded_scores_with_info
    WHERE
        category_id != 3
        AND category_id IN ({", ".join([str(cat) for cat in filter_cats])})

    UNION ALL

    SELECT
        *
    FROM
        not_loaded_scores_culture
    WHERE
        category_id IN ({", ".join([str(cat) for cat in filter_cats])})
    ;
    """

    return db.fetch_data(sql=sql)


if __name__ == "__main__":
    # Connect to database
    db = Database()
    db.connect()

    # Get data
    filter_cats = [
        #0, # General
        1, # Safety
        2, # Weather
        3, # Culture
        #4, # Cost
        5, # Geography
        #6, # Reachability
        7 # Health
    ]
    data = prepare_text_generation(db, filter_cats, testing=True)

    # Generate texts
    prompt_engine = PromptEngine(db)

    # For each location
    for loc in data["location_id"].unique():

        # For each category
        for cat in data["category_id"].unique():

            # If reachability, generate texts for each reference start location
            if cat == 6:
                for ref_start_loc in data[data["category_id"] == cat]["ref_start_location_id"].unique():
                    prompt_engine.prompt(data[(data["category_id"] == cat) & (data["ref_start_location_id"] == ref_start_loc)])

            else:
                prompt_engine.prompt(data[data["category_id"] == cat])

    # Disconnect from database
    db.disconnect()