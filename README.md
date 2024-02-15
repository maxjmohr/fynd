<div align="center">
    <img src="res/images/logo.svg" alt="logo" width="300">
</div>

#
Welcome to fynd, your tool for finding your next travel destination.

## Dependencies

To run any scripts or contribute to the project, simply install the dependencies via pip or anaconda:

```bash
fynd -m venv .venv
source .venv/bin/activate
fynd -m pip install -r requirements.txt
```

```bash
conda env create -n fynd -f environment.yml
conda activate fynd
```

## Core repository structure

The codebase is divided into two main directories: `src` and `res`. The `src` directory contains the source code for the `backend` and `frontend`, while the `res` directory contains the resources used by the source code.

```
📦Repository
 ┣ 📂.config
 ┣ 📂res
 ┃ ┣ 📂drivers
 ┃ ┣ 📂images
 ┃ ┣ 📂master_data
 ┃ ┣ 📂models
 ┣ 📂src
 ┃ ┣ 📂backend
 ┃ ┃ ┣ 📂data
 ┃ ┃ ┃ ┣ 📜accomodations.py
 ┃ ┃ ┃ ┣ 📜costs.py
 ┃ ┃ ┃ ┣ 📜demographics.py
 ┃ ┃ ┃ ┣ 📜geography.py
 ┃ ┃ ┃ ┣ 📜health.py
 ┃ ┃ ┃ ┣ 📜places.py
 ┃ ┃ ┃ ┣ 📜reachability.py
 ┃ ┃ ┃ ┣ 📜route.py
 ┃ ┃ ┃ ┣ 📜safety.py
 ┃ ┃ ┃ ┗ 📜weather.py
 ┃ ┃ ┣ 📂database
 ┃ ┃ ┃ ┣ 📂connection
 ┃ ┃ ┃ ┃ ┣ 📜get_raw_data.py
 ┃ ┃ ┃ ┃ ┗ 📜get_texts_general_anomaly.py
 ┃ ┃ ┃ ┣ 📂internal
 ┃ ┃ ┃ ┃ ┣ 📜cost_scores.py
 ┃ ┃ ┃ ┃ ┣ 📜culture_scores.py
 ┃ ┃ ┃ ┃ ┣ 📜culture_scores_subdimensions.py
 ┃ ┃ ┃ ┃ ┣ 📜geography_scores.py
 ┃ ┃ ┃ ┃ ┣ 📜get_airports.py
 ┃ ┃ ┃ ┃ ┣ 📜get_all_scores.py
 ┃ ┃ ┃ ┃ ┣ 📜get_location_images.py
 ┃ ┃ ┃ ┃ ┣ 📜get_locations.py
 ┃ ┃ ┃ ┃ ┣ 📜health_scores.py
 ┃ ┃ ┃ ┃ ┣ 📜reachability_scores.py
 ┃ ┃ ┃ ┃ ┣ 📜safety_scores.py
 ┃ ┃ ┃ ┃ ┣ 📜test_culture_text.py
 ┃ ┃ ┃ ┃ ┣ 📜update_accommodation_cost.py
 ┃ ┃ ┃ ┃ ┗ 📜weather_scores.py
 ┃ ┃ ┃ ┣ 📂objects
 ┃ ┃ ┃ ┗ 📜db_helpers.py
 ┃ ┣ 📂frontend
 ┃ ┃ ┣ 📂destination_search
 ┃ ┃ ┃ ┣ 📂destinations
 ┃ ┃ ┃ ┃ ┣ 📂static
 ┃ ┃ ┃ ┃ ┃ ┣ 📂css
 ┃ ┃ ┃ ┃ ┃ ┗ 📂images
 ┃ ┃ ┃ ┃ ┣ 📜admin.py
 ┃ ┃ ┃ ┃ ┣ 📜apps.py
 ┃ ┃ ┃ ┃ ┣ 📜compute_haversine.py
 ┃ ┃ ┃ ┃ ┣ 📜compute_relevance.py
 ┃ ┃ ┃ ┃ ┣ 📜create_similarity_text_prompt.py
 ┃ ┃ ┃ ┃ ┣ 📜download_location_images.py
 ┃ ┃ ┃ ┃ ┣ 📜forms.py
 ┃ ┃ ┃ ┃ ┣ 📜models.py
 ┃ ┃ ┃ ┃ ┣ 📜tests.py
 ┃ ┃ ┃ ┃ ┣ 📜urls.py
 ┃ ┃ ┃ ┃ ┗ 📜views.py
 ┃ ┃ ┃ ┣ 📂templates
 ┃ ┃ ┃ ┃ ┣ 📜about.html
 ┃ ┃ ┃ ┃ ┣ 📜base.html
 ┃ ┃ ┃ ┃ ┣ 📜compare.html
 ┃ ┃ ┃ ┃ ┣ 📜discover.html
 ┃ ┃ ┃ ┃ ┣ 📜home.html
 ┃ ┃ ┃ ┃ ┣ 📜list.html
 ┃ ┃ ┃ ┃ ┣ 📜location_detail.html
 ┃ ┃ ┃ ┃ ┗ 📜search.html
 ┃ ┃ ┃ ┗ 📜manage.py
 ┃ ┃ ┗ 📜frontend_requirements.txt
```

## Exemplary automated use cases

Hereinafter, we provide some use cases of working with the fynd codebase. The following examples are not exhaustive and are meant to provide a starting point for working with the codebase. Upon request, we can provide access keys and other necessary data to run the code.

> [!NOTE]
> The code snippets provided are exemplary and may not work out of the box. Reasons can vary from missing API keys to  The examples are meant to provide a conceptual starting point for working with the codebase.

### Add new location master data

In order to add a new location to the database, create a dataframe with the city and country names you want to add and pass them into `get_master_data` in `src/backend/database/internal/get_locations.py`.

```python
from src.backend.database.db_helpers import Database
from src.backend.database.internal.get_locations import get_master_data
import pandas as pd

# Create dataframe
cities = pd.DataFrame({
    "city": ["ABC", "DEF", "GHI"],
    "country": ["JKL", "MNO", "PQR"],
    "type": ["city", "city", "city"]
})

# Connect to database
db = Database()
db.connect()
airports = db.fetch_data(total_object="core_airports")

# Get master data
master_data = get_master_data(cities, airports, shape="polygon")

# Insert into database
db.insert_data(master_data, table=TARGET_TABLE, if_exists="replace", updated_at=True)
db.disconnect()
```

### Collect new data

To collect data for specific categories, use `src/backend/database/connection/get_raw_data.py`. The script is designed to collect data from various sources and store them in the database. Specify the categories you want to collect data for in the script:

```python
# Activate the desired categories
...
table_fill_function_dict = {
    #"raw_costs_numbeo": [fill_raw_costs_numbeo, 1],
    #"raw_safety_city": [fill_raw_safety_city, 2],
    #"raw_safety_country": [fill_raw_safety_country, 3],
    #"raw_places": [fill_raw_places, 4],
    #"raw_weather_current_future": [fill_raw_weather_current_future, 5],
    #"raw_weather_historical": [fill_raw_weather_historical, 6],
    #"raw_geography_coverage": [fill_raw_geography_coverage, 7],
    #"raw_accommodation_costs" : [fill_raw_accommodation_costs, 8],
    #"raw_reachability_air" : [fill_raw_reachability_air_par, 9],
    #"raw_reachability_land" : [fill_raw_reachability_land_par, 10],
    #"raw_health" : [fill_raw_health, 11]
    }
...
```

Now execute the script:

```bash
python src/backend/database/connection/get_raw_data.py
```

### Compute new scores

To compute new scores for all locations for certain categories, use `src/backend/database/internal/get_all_scores.py`. The script is designed to compute scores for all locations for various categories and store them in the database. Specify the categories you want to compute scores for in the script:

```python
# Activate the desired categories
which_scores = {
    #'accommodation_cost': FillScores(db).accommodation_cost_scores,
    #'travel_cost': FillScores(db).travel_cost_scores,
    #'cost_of_living': FillScores(db).cost_of_living_scores
    #'safety': FillScores(db).safety_scores
    #'culture': FillScores(db).culture_scores,
    #'weather': FillScores(db).weather_scores,
    #'geography_coverage': FillScores(db).geography_coverage_scores,
    #'health': FillScores(db).health_scores,
    #'reachability': FillScores(db).get_reachability_scores,
}
```

Now execute the script:

```bash
python src/backend/database/internal/get_all_scores.py
```

### Generate new general and anomaly texts

To generate new general and anomaly texts for given locations and categories, use `src/backend/database/connection/get_texts_general_anomaly.py`. The script is designed to generate general and anomaly texts for given locations and categories and store them in the database. Specify the categories you want to generate texts for in the script:

```python
# Activate the desired categories
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
```

Separately delete the existing texts you want to replace:

```python
from src.backend.database.db_helpers import Database

# Activate the desired categories
filter_cats = # Same as above

# Locations to generate new texts for
location_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Connect database
db = Database()
db.connect()

# Delete the texts you want to replace
sql = f"""
DELETE
FROM core_texts
WHERE category_id in ({', '.join([str(cat) for cat in filter_cats])})
AND location_id in ({', '.join([str(loc) for loc in location_ids])})
;
"""
db.execute_sql(sql=sql)

db.disconnect()
```

Now execute the script:

```bash
python src/backend/database/connection/get_texts_general_anomaly.py
```

## License
Unfortunately, no money to reserve any rights.