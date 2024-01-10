CREATE TABLE core_dimensions (
    category_id     INTEGER NOT NULL,
    dimension_id    INTEGER NOT NULL,
    dimension       VARCHAR(255),
    description     VARCHAR(255),
    updated_at      TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (dimension_id),
    FOREIGN KEY (category_id) REFERENCES core_categories(category_id)
);

COMMENT ON TABLE core_dimensions IS 'The table contains the dimensions of the categories.';

COMMENT ON COLUMN core_dimensions.category_id IS 'Unique identifier of the category.';
COMMENT ON COLUMN core_dimensions.dimension_id IS 'Unique identifier of the dimension.';
COMMENT ON COLUMN core_dimensions.dimension IS 'Name of the dimension.';
COMMENT ON COLUMN core_dimensions.description IS 'Description of the dimension.';
COMMENT ON COLUMN core_dimensions.updated_at IS 'Timestamp of the last update.';

-- Create subcategories
INSERT INTO core_dimensions (category_id, dimension_id, dimension, description, updated_at)
VALUES  (1, 11, 'safety', 'Safety indicators as part of safety dimension', now()),
        (3, 31, 'arts_and_entertainment', 'Part of culture dimension', now()),
        (3, 32, 'restaurants', 'Part of culture dimension', now()),
        (3, 33, 'bars', 'Part of culture dimension', now()),
        (3, 34, 'cafes', 'Part of culture dimension', now()),
        (3, 35, 'other_dining_drinking', 'Part of culture dimension', now()),
        (3, 36, 'events', 'Part of culture dimension', now()),
        (3, 37, 'sports', 'Part of culture dimension', now()),
        (4, 41, 'travel_costs', 'Travel costs as part of cost dimension', now()),
        (4, 42, 'accommodation_costs', 'Accommodation costs as part of cost dimension', now()),
        (4, 43, 'meal_costs', '["meal_inexp", "meal_mid", "meal_mcdo"]', now()),
        (4, 44, 'grocery_costs', '["bread", "eggs", "cheese", "apples", "oranges", "potato", "lettuce", "tomato", "banana", "onion", "beef", "chicken", "rice"]', now()),
        (4, 45, 'drinks_costs', '["water_small", "water_large", "soda", "milk", "cappuccino", "beer_dom", "beer_imp", "beer_large", "wine"]', now()),
        (4, 46, 'transportation_costs', '["transport_month", "transport_ticket", "taxi_start", "taxi_km", "taxi_hour", "gas"]', now()),
        (4, 47, 'social_activities_costs', '["gym", "tennis", "cinema"]', now()),
        (4, 48, 'retail_products_costs', '["jeans", "dress", "shoes_running", "shoes_business"]', now()),
        (5, 51, 'landmarks', 'Part of geography dimension', now()),
        (6, 61, 'health', 'Part of health dimension', now())
;