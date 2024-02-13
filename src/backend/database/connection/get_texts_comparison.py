from datetime import datetime

def create_prompt_texts_comparison(data:dict, time_period:str, ref_start_loc:str) -> list:
    ''' Create the prompt texts for the comparison of a location to previous locations
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

    print(f"{datetime.now()} - Generating the comparison text prompt for '{list(data['Target Location']['Weather']['Daylight duration'].keys())[0]} and the previous locations {previous_locs}.")

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
Never generate a text containing the numeric values but rather use the distances to generate a qualitative description of the destination.
Never use the word 'score' but rather try to describe what exists more or less than in the other destinations.
The scores of all locations are for the selected time period of {time_period} and the reachability and travel costs calculated from {ref_start_loc}.
The dictionary is structured as follows: {{location type: {{category {{dimension {{location {{score}}}}}}}}}}.
{data}
Never list all dimension. Only highlight the most noteable categories and dimension standouts. Do not write an overall ending.
"""
    }

    return [message_system, message_user]