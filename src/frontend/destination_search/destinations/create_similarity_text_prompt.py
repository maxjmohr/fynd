import pandas as pd


def df_to_dict(data: pd.DataFrame) -> dict:
    """Convert a dataframe with previous and target destinations to a dict."""

    dict = {}

    # Iterate over the DataFrame rows
    for _, row in data.iterrows():
        # Extract the relevant information from the row
        location_type = row['location_type']
        category_name = row['category_name']
        dimension_name = row['dimension_name']
        location = row['location']
        score = row['score']
        
        # Update the nested dicts with the row data
        if location_type not in dict:
            dict[location_type] = {}
        if category_name not in dict[location_type]:
            dict[location_type][category_name] = {}
        if dimension_name not in dict[location_type][category_name]:
            dict[location_type][category_name][dimension_name] = {}
        if location not in dict[location_type][category_name][dimension_name]:
            dict[location_type][category_name][dimension_name][location] = {}

        dict[location_type][category_name][dimension_name][location] = score

    return dict


def create_similarity_text_prompt(
        data: pd.DataFrame,
        start_date: str,
        end_date: str, 
        ref_start_location_city: str,
        ref_start_location_country: str
    ) -> dict:
    """
    Create the GPT prompt for the comparison of a target destination to 
    previous destinations.
    """

    # If more than 2 previous destinations, take average (as max_tokens would be exceeded in prompt for gpt 3.5 turbo)
    if data["location"].nunique() > 3:  # one more because the target location is also included

        # Warning sentence
        warning = f"The number of previous destinations is {data['location'].nunique() - 1} which exceeds 2. Therefore, the scores of your previous destinations are averaged and then compared to {data[data['location_type'] == 'Target Location']['location'].values[0]}."

        # Average the scores of the previous locations
        previous_locs_avg = data[data["location_type"] != "Target Location"] \
            .drop(columns="location") \
            .groupby(["location_type", "category_name", "dimension_name"]).mean().reset_index()

        previous_locs_avg["location"] = "Average of your previous locations"

        # Add the target location to the average dataframe
        target_loc = data[data["location_type"] == "Target Location"]

        # Append the target location to the average dataframe
        data = pd.concat([previous_locs_avg, target_loc], ignore_index=True)

    else:
        warning = None

    # Convert the dataframe to a dictionary
    data = df_to_dict(data)

    # Get time period
    time_period = f"{start_date} to {end_date}"

    # Get the reference start location
    ref_start_loc = f"{ref_start_location_city} ({ref_start_location_country})"

    # Extract some data
    previous_locs = list(data['Previous Location(s)']['Weather']['Daylight duration'].keys())
    previous_locs = " and ".join(f"'{loc}'" for loc in previous_locs)

    # System message
    message_system = {
            "role": "system",
            "content": """You are a data interpretation system, adept at analyzing numerical variables and generating descriptive insights of travel destinations.
You are generating the text for a reader interested in traveling to the specific destination.
You are asked to generate a comparison text for a target destination based on the scores differences for each category and dimension to the previous destinations.
The scores are scaled between 0 and 1, where 0 is the worst and 1 is the best score.\n
"""
    }

    # User message
    message_user = {"role": "user",
               "content": f"""Use a maximum of three paragraphs and maximum of 15 sentences to generally describe the differences in the characteristics of the target travel destination '{list(data['Target Location']['Weather']['Daylight duration'].keys())[0]} for all dimensions to the users' previous destinations {previous_locs}.
Use easy and understandable language and short sentences.
Instead of addressing 'travelers' i.e. '... safe for travelers', use 'you' or 'your' to personally address the reader.
Never use the word 'score' but rather try to describe what exists more or less than in the other destinations.
The scores of all locations are for the selected time period of {time_period} and the reachability and travel costs calculated from {ref_start_loc}.
The dictionary is structured as follows: {{location type: {{category {{dimension {{location {{score}}}}}}}}}}.
{data}
Never list all dimensions. Only highlight the most noteable categories and dimension standouts. Do not write an overall ending.
Never generate a text containing the numeric values but rather use the distances to generate a qualitative description of the destination.
"""
    }

    return [message_system, message_user], warning