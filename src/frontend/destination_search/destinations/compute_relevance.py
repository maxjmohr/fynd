import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity, pairwise_distances


def compute_relevance(
        previous_locations: list[int], 
        scores: pd.DataFrame,
        previous_flag: float = -1.
    ) -> pd.Series:
    """
    Compute relevance score for each location in scores.

    Args:
    -----
    previous_locations: list[int] 
        List of location IDs.
    scores: pandas.DataFrame 
        DataFrame with location IDs as index and dimension IDs as columns.
    previous_flag: float
        Relevance value to assign to previous locations.
        (default=-1)

    Returns:
    --------
    relevance: pandas.Series
        Array of relevance scores.
    """

    # Compute mean distances
    scores_previous = scores.loc[previous_locations]
    scores_new = scores.drop(previous_locations)
    dist = pairwise_distances(scores_previous, scores_new, metric='euclidean')
    mean_dist = dist.mean(axis=0)

    # Compute relevance score
    max_dist = mean_dist.max() #FIXME Use fixed value?
    relevance = (1 - mean_dist/max_dist) * 100

    # Convert to Series to add location_ids (previous locations are relevance 0)
    relevance = pd.concat([
        pd.Series([previous_flag]*len(previous_locations), index=previous_locations, name='relevance'),
        pd.Series(relevance, index=scores_new.index, name='relevance')
    ])

    return relevance
