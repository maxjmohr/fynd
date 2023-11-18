import requests
import pandas as pd
from tqdm import tqdm
import pickle

# Read API key
with open('api_key_fsq.txt', 'r') as f:
    API_KEY = f.readline()

# Get all category levels
categories = pd.read_csv('fsq_categories.csv')
categories_levels = (
    categories
    .category_label
    .str.split(' > ', expand=True)
    .rename(columns={i: f'category_level_{i}' for i in range(6)})
)
categories = pd.concat([categories.category_id, categories_levels], axis=1)

# Select culture categories
culture_categories = [
    'Arts and Entertainment',
    'Dining and Drinking',
    'Event',
    'Landmarks and Outdoors'
]

# Get according category ids
culture_category_ids = (
    categories
    .query('category_level_0.isin(@culture_categories) ')
    .category_id
    .unique()
)

def get_places(category: int, ll: str, radius: int=10000, api_key: str = API_KEY):
    """Get the coarse category score for a given location."""
    
    # Assemble and execute API-call
    url = 'https://api.foursquare.com/v3/places/search'
    fields = [
        'fsq_id',
        'name',
        'location',
        'categories',
        'distance',
        'description',
        'rating',
        'stats',
        'popularity',
        'price'
    ]
    params = {
        'll': ll,
        'sort':'DISTANCE',
        'limit': 50,
        'radius': radius,
        'categories': category,
        'fields': ','.join(fields)
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': api_key
    }
    response = requests.get(url, params=params, headers=headers)

    # Convert response to data frame
    response_dict = eval(response.text)
    places = pd.DataFrame(response_dict['results'])

    return places


def get_cats_level(cats: list, level: int = 0) -> list:
    """Get category name on a certain level for a list of categories."""
    return list(set([categories.loc[categories.category_id == cat['id'], f'category_level_{level}'].item() for cat in cats]))


def compute_coarse_act_scores(places: pd.DataFrame):
    """Compute scores for each coarse category based on the places."""

    # Get coarse categories
    places['category_coarse'] = places.categories.apply(lambda x: get_cats_level(x,0)[0])
    places['category_fine'] = places.categories.apply(lambda x: get_cats_level(x,1))

    # Compute scores per coarse category
    scores = places.category_coarse.value_counts().rename('score')
    rating_weighted_scores = (
        places
        .fillna({'rating': 5})
        .groupby('category_coarse')
        .rating
        .sum()
        .rename('rating_weighted_score')
    )

    # Add missing categories
    scores_all_cats = pd.Series(culture_categories, name='category_coarse').to_frame()
    for s in [scores, rating_weighted_scores]:
        scores_all_cats = pd.merge(
            scores_all_cats,
            s, 
            how='left', 
            left_on='category_coarse', 
            right_index=True
        )

    # Fill missing scores with 0
    scores_all_cats = scores_all_cats.fillna(0)

    return scores_all_cats


def cultural_profile(ll: str, radius: int = 10000):
    """Compute cultural profile for a given location."""

    # Get places for each category and concatenate
    places = pd.concat([
        get_places(category=id, ll=ll, radius=radius) 
        for id in tqdm(culture_category_ids, desc='Querying places')
    ], axis=0)

    # Remove duplicates
    places = places.drop_duplicates(subset=['fsq_id'])

    # Get scores
    scores = compute_coarse_act_scores(places.copy())
    
    return scores


if __name__ == '__main__':

    import numpy as np
    import plotly.graph_objects as go

    # An example --------------------------------------------------------------

    islands = {
        'Spiekeroog': '53.773,7.704',
        #'Langeoog': '53.743,7.497',
        #'Wangerooge': '53.783,7.783',
        #'Baltrum': '53.733,7.383',
        #'Norderney': '53.700,7.150',
        #'Juist': '53.683,6.983',
        #'Borkum': '53.583,6.700',
        #'Helgoland': '54.183,7.883'  
    }

    islands_cultural_scores = {
        name: cultural_profile(ll) for name, ll in islands.items()
    }

    # Get max scores for each category
    max_scores = (
        pd.concat([df.assign(island=name) for name, df in islands_cultural_scores.items()])
        .groupby('category_coarse')
        .agg({'rating_weighted_score': 'max'})
        .reset_index()
        .rename(columns={'rating_weighted_score': 'max_score'})
    )

    # Normalize scores
    islands_cultural_scores_transformed = {
        name: (
            pd.merge(df, max_scores, how='left', on='category_coarse')
            .assign(rating_weighted_score_norm=lambda x: x.rating_weighted_score / x.max_score)
            .assign(rating_weighted_score_log=lambda x: np.log(x.rating_weighted_score+1e-6))
            .fillna(0)
        )
        for name, df in islands_cultural_scores.items()
    }

    # Plot polar chart
    fig = go.Figure()
    for name, scores in islands_cultural_scores_transformed.items():
        scores = scores.query('category_coarse != "Event"')
        fig.add_trace(go.Scatterpolar(
            r=scores.rating_weighted_score_log,
            theta=scores.category_coarse,
            fill='toself',
            name=name
        ))
    fig.show()