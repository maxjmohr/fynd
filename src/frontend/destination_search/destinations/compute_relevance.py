import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import pairwise_distances


def compute_relevance(
        previous_locations: list[int], 
        scores: pd.DataFrame,
        preferences: dict,
        factor: float = 100.
    ) -> pd.Series:
    """
    Compute relevance score for each location in scores.

    Args:
    -----
    previous_locations: list[int] 
        List of location IDs.

    scores: pandas.DataFrame 
        DataFrame with scores for each location, category and dimension.

    preferences: dict
        Dictionary with respective importance and direction for each category.

    Returns:
    --------
    relevance: pandas.Series
        Array of relevance scores.
    """

    # Pivot scores (from long to wide)
    scores = scores.pivot(
        index='location_id',
        columns=['category_id', 'dimension_id'],
        values='score'
    )

    # Impute missing values with column means
    # (i.e. mean of scores in the respective dimension)
    scores = scores.fillna(scores.mean())

    # Split scores into previous and new locations
    scores_previous = scores.loc[previous_locations]
    scores_new = scores.drop(previous_locations)

    # Loop over categories and compute relevance
    relevance = 0
    importance_sum = 0
    for category in scores.columns.levels[0]:

        # Retrieve scores for category
        cat_scores_previous = scores_previous.loc[:,category]
        cat_scores_new = scores_new.loc[:,category]

        # Compute mean distances (over previous locations)
        dist = pairwise_distances(
            cat_scores_previous, cat_scores_new, metric='euclidean'
        )
        mean_dist = dist.mean(axis=0)

        # Normalize to [0, 1]
        mean_dist = (mean_dist - mean_dist.min()) / (mean_dist.max() - mean_dist.min())

        # Invert (if preference if for similarity, i.e. direction=False)
        if not preferences[f'direction_{category}']:
            mean_dist = 1 - mean_dist

        # Weight by importance
        weight = preferences[f'importance_{category}']
        relevance += weight * mean_dist
        importance_sum += weight

    # Normalize to [0, 1]
    relevance = relevance / importance_sum

    # Scale to [0, factor]
    relevance = factor * relevance

    return pd.Series(relevance, index=scores_new.index, name='relevance')
