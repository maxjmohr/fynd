CREATE TABLE core_dimensions (
    category_id         INTEGER NOT NULL,
    dimension_id        INTEGER NOT NULL,
    dimension_name      VARCHAR(255),
    description         VARCHAR(500),
    extras              VARCHAR(255),
    raw_value_decimals  INTEGER,
    raw_value_unit      VARCHAR(255),
    icon_url            VARCHAR(255),
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (dimension_id),
    FOREIGN KEY (category_id) REFERENCES core_categories(category_id)
);

COMMENT ON TABLE core_dimensions IS 'The table contains the dimensions of the categories.';

COMMENT ON COLUMN core_dimensions.category_id IS 'Unique identifier of the category.';
COMMENT ON COLUMN core_dimensions.dimension_id IS 'Unique identifier of the dimension.';
COMMENT ON COLUMN core_dimensions.dimension_name IS 'Name of the dimension.';
COMMENT ON COLUMN core_dimensions.description IS 'Description of the dimension.';
COMMENT ON COLUMN core_dimensions.extras IS 'Extra information about the dimension.';
COMMENT ON COLUMN core_dimensions.raw_value_decimals IS 'The number of decimal places to round the raw value to.';
COMMENT ON COLUMN core_dimensions.raw_value_unit IS 'The unit of the raw value.';
COMMENT ON COLUMN core_dimensions.icon_url IS 'URL to the icon of the dimension.';
COMMENT ON COLUMN core_dimensions.updated_at IS 'Timestamp of the last update.';

-- Create subcategories
INSERT INTO core_dimensions (category_id, dimension_id, dimension_name, description, extras, raw_value_decimals, raw_value_unit, icon_url, updated_at)
VALUES  (0, 00, 'General dummy dimension', NULL, NULL, NULL, now()),
        (1, 11, 'Crime rate safety', 'Provides insights into the prevalence of criminal activities.', NULL, NULL, NULL, 'https://static.thenounproject.com/png/1820946-200.png', now()),
        (1, 12, 'Ecological threat safety', 'Gauges the potential harm to the environment.', NULL, NULL, NULL, 'https://static.thenounproject.com/png/6061985-200.png', now()),
        (1, 13, 'Peace index', 'Measures the overall level of peace.', NULL, NULL, NULL, 'https://static.thenounproject.com/png/32960-200.png', now()),
        (1, 14, 'Personal freedom', 'Assesses the degree to which individuals can exercise their rights and freedoms without interference.', NULL, NULL, NULL, 'https://static.thenounproject.com/png/5484847-200.png', now()),
        (1, 15, 'Political stability', 'Evaluates the political climate and perhaps instability.', NULL, NULL, NULL, 'https://static.thenounproject.com/png/3189332-200.png', now()),
        (1, 16, 'Rule of law', 'Resembles effectiveness of legal systems in upholding the law and protecting individuals and juridical order.', NULL, NULL, NULL, 'https://static.thenounproject.com/png/2398414-200.png', now()),
        (1, 17, 'Terrorism safety', 'Considers various factors related to terrorism risks.', NULL, NULL, NULL, 'https://static.thenounproject.com/png/1922731-200.png', now()),
        (2, 21, 'Maximum temperature', 'The maximum average temperature in the selected time span', NULL, 1, '°C', 'https://static.thenounproject.com/png/6074205-200.png', now()),
        (2, 22, 'Minimum temperature', 'The minimum average temperature in the selected time span', NULL, 1, '°C', 'https://static.thenounproject.com/png/6074213-200.png', now()),
        (2, 23, 'Sunshine duration', 'The daily average sunshine duration in the selected time span (consistently less than daylight duration due to dawn and dusk and is measured calculating direct normalized irradiance exceeding 120 W/m²)', NULL, 1, 'h', 'https://static.thenounproject.com/png/6074198-200.png', now()),
        (2, 24, 'Daylight duration', 'The daily average daylight in the selected time span', NULL, 1, 'h', 'https://static.thenounproject.com/png/6074193-200.png', now()),
        (2, 25, 'Precipitation duration', 'The daily average precipitation duration in the selected time span', NULL, 1, 'h', 'https://static.thenounproject.com/png/1307630-200.png', now()),
        (2, 26, 'Precipitation amount', 'The daily average precipitation amount in the selected time span (considering the total amount of rain and snowfall)', NULL, 1, 'mm', 'https://static.thenounproject.com/png/462130-200.png', now()),
        (2, 27, 'Rain amount', 'The daily average rain sum in the selected time span', NULL, 1, 'mm', 'https://static.thenounproject.com/png/6074208-200.png', now()),
        (2, 28, 'Snowfall amount', 'The daily average snowfall sum in the selected time span', NULL, 1, 'cm', 'https://static.thenounproject.com/png/6074210-200.png', now()),
        (2, 29, 'Maximum wind speed', 'The daily average maximum wind speed in the selected time span', NULL, 1, 'km/h', 'https://static.thenounproject.com/png/6074200-200.png', now()),
        (3, 31, 'Restaurants', 'Number of restaurants', NULL, NULL, NULL, 'https://static.thenounproject.com/png/4356325-200.png', now()),
        (3, 32, 'Fast food joints', 'Number of fast food joints', NULL, NULL, NULL, 'https://static.thenounproject.com/png/6488021-200.png', now()),
        (3, 33, 'Bars', 'Number of bars', NULL, NULL, NULL, 'https://static.thenounproject.com/png/3732313-200.png', now()),
        (3, 34, 'Cafes', 'Number of cafes', NULL, NULL, NULL, 'https://static.thenounproject.com/png/836672-200.png', now()),
        (3, 35, 'Cultural and artistic venues', 'Number of cultural and artistic venues such as museums, theatres and cinemas', NULL, NULL, NULL, 'https://static.thenounproject.com/png/6488396-200.png', now()),
        (3, 36, 'Leisure venues', 'Number of leisure venues such as spa venues, parks and entertainment venues', NULL, NULL, NULL, 'https://static.thenounproject.com/png/6041911-200.png', now()),
        (3, 37, 'Nature', 'Number of natural landmarks such as mountains, forests and national parks', NULL, NULL, NULL, 'https://static.thenounproject.com/png/1452028-200.png', now()),
        (3, 38, 'Tourism sights', 'Number of tourism sights', NULL, NULL, NULL, 'https://static.thenounproject.com/png/2675564-200.png', now()),
        (4, 41, 'Travel', 'The score approximates the travel costs for the given start location to the destination in the selected time span. A higher score refers to higher costs.', NULL, 0, '€', 'https://static.thenounproject.com/png/4303424-200.png', now()),
        (4, 42, 'Accommodation', 'The score approximates the travel costs at the destination in the selected time span. A higher score refers to higher costs.', NULL, 0, '€', 'https://static.thenounproject.com/png/4559422-200.png', now()),
        (4, 43, 'Meals', 'The cumulative meal costs of an average McDonalds order, cheap as well as ordinary meal.', '["meal_inexp", "meal_mid", "meal_mcdo"]', 0, '€', 'https://static.thenounproject.com/png/1826996-200.png', now()),
        (4, 44, 'Groceries', 'The cumulative grocery costs including meat, fruits and vegetables.', '["bread", "eggs", "cheese", "apples", "oranges", "potato", "lettuce", "tomato", "banana", "onion", "beef", "chicken", "rice"]', 0, '€', 'https://static.thenounproject.com/png/5478570-200.png', now()),
        (4, 45, 'Drinks', 'The cumulative drinking costs containing non-alcoholic (water, sodas and coffee) as well as alcoholic beverages (beers and a bottle of wine).', '["water_small", "water_large", "soda", "milk", "cappuccino", "beer_dom", "beer_imp", "beer_large", "wine"]', 0, '€', 'https://static.thenounproject.com/png/1054446-200.png', now()),
        (4, 46, 'Transportation', 'The cumulative local transportation costs including public transport tickets, taxi rides and the gas price.', '["transport_month", "transport_ticket", "taxi_start", "taxi_km", "taxi_hour", "gas"]', 0, '€', 'https://static.thenounproject.com/png/713275-200.png', now()),
        (4, 47, 'Social activities', 'The cumulative costs regarding social activities including a monthly gym membership, tennis court fees and a cinema visit.', '["gym", "tennis", "cinema"]', 0, '€', 'https://static.thenounproject.com/png/1945836-200.png', now()),
        (4, 48, 'Retail products', 'The cumulative retail products costs containing jeans, dress and shoe prices.', '["jeans", "dress", "shoes_running", "shoes_business"]', 0, '€', 'https://static.thenounproject.com/png/1221585-200.png', now()),
        (5, 51, 'Trees', 'Share of tree coverage', NULL, NULL, NULL, 'https://static.thenounproject.com/png/1258519-200.png', now()),
        (5, 52, 'Shrubland', 'Share of shrubland coverage', NULL, NULL, NULL, 'https://static.thenounproject.com/png/1290801-200.png', now()),
        (5, 53, 'Grassland', 'Share of grassland coverage', NULL, NULL, NULL, 'https://static.thenounproject.com/png/2469367-200.png', now()),
        (5, 54, 'Cropland', 'Share of cropland coverage', NULL, NULL, NULL, 'https://static.thenounproject.com/png/5800836-200.png', now()),
        (5, 55, 'Built up', 'Share of built up land coverage', NULL, NULL, NULL, 'https://static.thenounproject.com/png/4393983-200.png', now()),
        (5, 56, 'Bare and sparse vegetation', 'Share of bare and sparse vegetation coverage', NULL, NULL, NULL, 'https://static.thenounproject.com/png/6028192-200.png', now()),
        (5, 57, 'Snow and ice', 'Share of snow and ice coverage', NULL, NULL, NULL, 'https://static.thenounproject.com/png/2933530-200.png', now()),
        (5, 58, 'Permanent watermarks', 'Share of permanent watermarks coverage such as lakes, rivers, and other water features', NULL, NULL, NULL, 'https://static.thenounproject.com/png/2446723-200.png', now()),
        (5, 59, 'Herbaceous wetland', 'Share of herbaceous wetland coverage', NULL, NULL, NULL, 'https://static.thenounproject.com/png/6306280-200.png', now()),
        (5, 510, 'Mangroves', 'Share of mangroves coverage', NULL, NULL, NULL, 'https://static.thenounproject.com/png/4841590-200.png', now()),
        (5, 511, 'Moss and lichen', 'Share of moss and lichen coverage', NULL, NULL, NULL, 'https://static.thenounproject.com/png/5552178-200.png', now()),
        (6, 61, 'Automobile', 'The score captures the reachability by an automobile from the selected starting location to the destination at the selected time span.', NULL, 2, 'h', 'https://static.thenounproject.com/png/2603832-200.png', now()),
        (6, 62, 'Public transport', 'The score captures the reachability by public transport from the selected starting location to the destination at the selected time span.', NULL, 2, 'h', 'https://static.thenounproject.com/png/6539288-200.png', now()),
        (6, 63, 'Flight', 'The score captures the reachability by plane from the airport nearest to the selected starting location to the airport nearest to the destination at the selected time span.', NULL, 2, 'h', 'https://static.thenounproject.com/png/5286605-200.png', now()),
        (7, 71, 'Health index', 'Measures the degree to which a reasonable quality of life is experienced by all, including material resources, shelter, basic service and connectivity.', NULL, NULL, NULL, 'https://static.thenounproject.com/png/6497729-200.png', now())
;