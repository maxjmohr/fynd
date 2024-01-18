CREATE TABLE core_dimensions (
    category_id     INTEGER NOT NULL,
    dimension_id    INTEGER NOT NULL,
    dimension       VARCHAR(255),
    description     VARCHAR(500),
    extras          VARCHAR(255),
    updated_at      TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (dimension_id),
    FOREIGN KEY (category_id) REFERENCES core_categories(category_id)
);

COMMENT ON TABLE core_dimensions IS 'The table contains the dimensions of the categories.';

COMMENT ON COLUMN core_dimensions.category_id IS 'Unique identifier of the category.';
COMMENT ON COLUMN core_dimensions.dimension_id IS 'Unique identifier of the dimension.';
COMMENT ON COLUMN core_dimensions.dimension IS 'Name of the dimension.';
COMMENT ON COLUMN core_dimensions.description IS 'Description of the dimension.';
COMMENT ON COLUMN core_dimensions.extras IS 'Extra information about the dimension.';
COMMENT ON COLUMN core_dimensions.updated_at IS 'Timestamp of the last update.';

-- Create subcategories
INSERT INTO core_dimensions (category_id, dimension_id, dimension, description, extras, updated_at)
VALUES  (1, 11, 'crime_rate', 'The crime rate provides insights into the prevalence of criminal activities, helping travelers make informed decisions to ensure their personal safety and security during their stay.', NULL, now()),
        (1, 12, 'ecological_threat', 'The ecological threat gauges the potential harm to the environment, allowing you to choose destinations that prioritize ecological sustainability and minimize the impact of human activities on natural ecosystems.', NULL, now()),
        (1, 13, 'peace_index', 'The Peace Index dimension measures the overall level of peace in a destination. Travelers seeking tranquil and safe environments can rely on this index to gauge the general peacefulness of a location, considering factors such as societal harmony and absence of conflict.', NULL, now()),
        (1, 14, 'personal_freedom', 'Personal freedom assesses the degree to which individuals can exercise their rights and freedoms without interference. For travelers valuing personal liberties, this dimension is essential for choosing a welcoming and open destination.', NULL, now()),
        (1, 15, 'political_stability', 'Political stability evaluates the political climate of a destination, helping travelers gauge the likelihood of political unrest or instability.', NULL, now()),
        (1, 16, 'rule_of_law', 'Ensure a sense of justice and order during your travels by considering the rule of law dimension. This assesses the effectiveness of legal systems in upholding the law and protecting individuals.', NULL, now()),
        (1, 17, 'terrorism_index', 'The terrorism index considers various factors related to terrorism risks, helping travelers make educated decisions to prioritize safety and security throughout their journey.', NULL, now()),
        (2, 21, 'temperature_max', 'The maximum average temperature provides insights into the peak temperature you can expect during your stay, helping you pack accordingly and prepare for the climatic conditions of your destination.', NULL, now()),
        (2, 22, 'temperature_min', 'The minimum average temperature offers information on the lowest temperatures, enabling travelers to bring appropriate clothing and gear to stay warm in cooler climates.', NULL, now()),
        (2, 23, 'sunshine_duration', 'The daily average sunshine duration (in hours) will consistently be less than daylight duration due to dawn and dusk and is measured calculating direct normalized irradiance exceeding 120 W/m².', NULL, now()),
        (2, 24, 'daylight_duration', 'Daily average daylight hours helps travelers plan their activities and explore destinations during daylight hours for a more vibrant and enjoyable experience.', NULL, now()),
        (2, 25, 'precipitation_duration', 'The daily average precipitation duration contains the amount of hours with rain, allowing travelers to plan indoor activites and appropriate clothing ahead of their holiday.', NULL, now()),
        (2, 26, 'precipitation_sum', 'Get a comprehensive view of the precipitation in your destination with the precipitation sum dimension. This considers the total amount of rainfall, helping travelers anticipate weather patterns and make informed decisions about the suitability of their chosen destination.', NULL, now()),
        (2, 27, 'rain_sum', 'The rain sum is a more specific dimension compared to the precipitation sum which includes rain and snowfall.', NULL, now()),
        (2, 28, 'snowfall_sum', 'The snowfall sum is a more specific dimension compared to the precipitation sum which includes rain and snowfall.', NULL, now()),
        (2, 29, 'wind_speed_max', 'The maximum wind speed provides information on the peak wind speed, helping travelers choose destinations with favorable wind conditions for outdoor activities and exploration.', NULL, now()),
        (3, 31, 'arts_and_entertainment', 'Part of culture dimension', NULL, now()),
        (3, 32, 'restaurants', 'Part of culture dimension', NULL, now()),
        (3, 33, 'bars', 'Part of culture dimension', NULL, now()),
        (3, 34, 'cafes', 'Part of culture dimension', NULL, now()),
        (3, 35, 'other_dining_drinking', 'Part of culture dimension', NULL, now()),
        (3, 36, 'events', 'Part of culture dimension', NULL, now()),
        (3, 37, 'sports', 'Part of culture dimension', NULL, now()),
        (4, 41, 'travel_costs', 'Travel costs as part of cost dimension', NULL, now()),
        (4, 42, 'accommodation_costs', 'Accommodation costs as part of cost dimension', NULL, now()),
        (4, 43, 'meal_costs', NULL, '["meal_inexp", "meal_mid", "meal_mcdo"]', now()),
        (4, 44, 'grocery_costs', NULL, '["bread", "eggs", "cheese", "apples", "oranges", "potato", "lettuce", "tomato", "banana", "onion", "beef", "chicken", "rice"]', now()),
        (4, 45, 'drinks_costs', NULL, '["water_small", "water_large", "soda", "milk", "cappuccino", "beer_dom", "beer_imp", "beer_large", "wine"]', now()),
        (4, 46, 'transportation_costs', NULL, '["transport_month", "transport_ticket", "taxi_start", "taxi_km", "taxi_hour", "gas"]', now()),
        (4, 47, 'social_activities_costs', NULL, '["gym", "tennis", "cinema"]', now()),
        (4, 48, 'retail_products_costs', NULL, '["jeans", "dress", "shoes_running", "shoes_business"]', now()),
        (5, 51, 'landmarks', 'Part of geography dimension', NULL, now()),
        (6, 61, 'reachability', 'xxx', NULL, now()),
        (7, 71, 'health', 'The health dimension measures the degree to which a reasonable quality of life is experienced by all, including material resources, shelter, basic service and connectivity.', NULL, now())
;