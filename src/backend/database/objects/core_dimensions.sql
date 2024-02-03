CREATE TABLE core_dimensions (
    category_id     INTEGER NOT NULL,
    dimension_id    INTEGER NOT NULL,
    dimension_name  VARCHAR(255),
    description     VARCHAR(500),
    extras          VARCHAR(255),
    icon_url        VARCHAR(255),
    updated_at      TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (dimension_id),
    FOREIGN KEY (category_id) REFERENCES core_categories(category_id)
);

COMMENT ON TABLE core_dimensions IS 'The table contains the dimensions of the categories.';

COMMENT ON COLUMN core_dimensions.category_id IS 'Unique identifier of the category.';
COMMENT ON COLUMN core_dimensions.dimension_id IS 'Unique identifier of the dimension.';
COMMENT ON COLUMN core_dimensions.dimension_name IS 'Name of the dimension.';
COMMENT ON COLUMN core_dimensions.description IS 'Description of the dimension.';
COMMENT ON COLUMN core_dimensions.extras IS 'Extra information about the dimension.';
COMMENT ON COLUMN core_dimensions.icon_url IS 'URL to the icon of the dimension.';
COMMENT ON COLUMN core_dimensions.updated_at IS 'Timestamp of the last update.';

-- Create subcategories
INSERT INTO core_dimensions (category_id, dimension_id, dimension_name, description, extras, icon_url, updated_at)
VALUES  (0, 00, 'General dummy dimension', NULL, NULL, NULL, now()),
        (1, 11, 'Crime rate safety', 'The crime rate safety index provides insights into the prevalence of criminal activities. A higher score refers to lower crime rates.', NULL, 'https://static.thenounproject.com/png/1820946-200.png', now()),
        (1, 12, 'Ecological threat safety', 'The ecological threat safety index gauges the potential harm to the environment. A higher score refers to less ecological threats.', NULL, 'https://static.thenounproject.com/png/6061985-200.png', now()),
        (1, 13, 'Peace index', 'The peace index measures the overall level of peace in a destination. A higher score refers to a more peaceful environment.', NULL, 'https://static.thenounproject.com/png/32960-200.png', now()),
        (1, 14, 'Personal freedom', 'Personal freedom assesses the degree to which individuals can exercise their rights and freedoms without interference. A higher score refers to more personal freedom.', NULL, 'https://static.thenounproject.com/png/5484847-200.png', now()),
        (1, 15, 'Political stability', 'Political stability evaluates the political climate and perhaps instability of a destination. A higher score refers to a higher political stability.', NULL, 'https://static.thenounproject.com/png/3189332-200.png', now()),
        (1, 16, 'Rule of law', 'Ensure a sense of justice (effectiveness of legal systems in upholding the law and protecting individuals) and order during your travels by considering the rule of law dimension. A higher score refers to higher level of effectiveness of the jurisdiction.', NULL, 'https://static.thenounproject.com/png/2398414-200.png', now()),
        (1, 17, 'Terrorism safety', 'The terrorism safety index considers various factors related to terrorism risks. A higher score refers to less terrorist threats.', NULL, 'https://static.thenounproject.com/png/1922731-200.png', now()),
        (2, 21, 'Maximum temperature', 'The maximum average temperature at the destinations in the selected time span. A higher score refers to higher maximum temperature.', NULL, 'https://static.thenounproject.com/png/6074205-200.png', now()),
        (2, 22, 'Minimum temperature', 'The minimum average temperature at the destinations in the selected time span. A higher score refers to higher minimum temperature.', NULL, 'https://static.thenounproject.com/png/6074213-200.png', now()),
        (2, 23, 'Sunshine duration', 'The daily average sunshine duration (in hours) at the destinations in the selected time span will consistently be less than daylight duration due to dawn and dusk and is measured calculating direct normalized irradiance exceeding 120 W/m². A higher score refers to a longer sunshine duration.', NULL, 'https://static.thenounproject.com/png/6074198-200.png', now()),
        (2, 24, 'Daylight duration', 'The daily average daylight at the destinations in the selected time span. A higher score refers to a longer daylight duration.', NULL, 'https://static.thenounproject.com/png/6074193-200.png', now()),
        (2, 25, 'Precipitation duration', 'The daily average precipitation duration at the destinations in the selected time span. A higher score refers to a shorter percipitation duration.', NULL, 'https://static.thenounproject.com/png/1307630-200.png', now()),
        (2, 26, 'Precipitation amount', 'The daily average precipitation amount at the destinations in the selected time span. This considers the total amount of rain and snowfall. A higher score refers to less percipitation.', NULL, 'https://static.thenounproject.com/png/462130-200.png', now()),
        (2, 27, 'Rain amount', 'The rain sum is a more specific dimension compared to the precipitation sum which solely includes rain at the destinations in the selected time span. A higher score refers to less rain.', NULL, 'https://static.thenounproject.com/png/6074208-200.png', now()),
        (2, 28, 'Snowfall amount', 'The snowfall sum is a more specific dimension compared to the precipitation sum which solely includes snowfall at the destinations in the selected time span. A higher score refers to less snowfall.', NULL, 'https://static.thenounproject.com/png/6074210-200.png', now()),
        (2, 29, 'Maximum wind speed', 'The maximum wind speed provides information on the peak wind speed at the destinations in the selected time span. A higher score refers to a lower maximum wind speed.', NULL, 'https://static.thenounproject.com/png/6074200-200.png', now()),
        (3, 31, 'Restaurants', 'The score reflects the amount of restaurants at the destination. A higher score refers to more restaurants.', NULL, 'https://static.thenounproject.com/png/4356325-200.png', now()),
        (3, 32, 'Fast food joints', 'The score reflects the amount of fast food joints at the destination. A higher score refers to more fast food joints.', NULL, 'https://static.thenounproject.com/png/6488021-200.png', now()),
        (3, 33, 'Bars', 'The score reflects the amount of bars at the destination. A higher score refers to more bars.', NULL, 'https://static.thenounproject.com/png/3732313-200.png', now()),
        (3, 34, 'Cafes', 'The score reflects the amount of cafes at the destination. A higher score refers to more cafes.', NULL, 'https://static.thenounproject.com/png/836672-200.png', now()),
        (3, 35, 'Cultural and artistic venues', 'The score reflects the amount of cultural and artistic venues such as museums, theatres and cinemas at the destination. A higher score refers to more venues.', NULL, 'https://static.thenounproject.com/png/6488396-200.png', now()),
        (3, 36, 'Leisure venues', 'The score reflects the amount of leisure venues such as spa venues, parks and entertainment venues at the destination. A higher score refers to more venues.', NULL, 'https://static.thenounproject.com/png/6041911-200.png', now()),
        (3, 37, 'Nature', 'The score reflects the amount of natural landmarks such as mountains, forests and national parks at the destination. A higher score refers to more natural landmarks.', NULL, 'https://static.thenounproject.com/png/1452028-200.png', now()),
        (3, 38, 'Tourism sights', 'The score reflects the amount of tourism sights at the destination. A higher score refers to more tourism sights.', NULL, 'https://static.thenounproject.com/png/2675564-200.png', now()),
        (4, 41, 'Travel', 'The score approximates the travel costs for the given start location to the destination in the selected time span. A higher score refers to higher costs.', NULL, 'https://static.thenounproject.com/png/4303424-200.png', now()),
        (4, 42, 'Accommodation', 'The score approximates the travel costs at the destination in the selected time span. A higher score refers to higher costs.', NULL, 'https://static.thenounproject.com/png/4559422-200.png', now()),
        (4, 43, 'Meals', 'The score approximates the meal costs at the destination in the selected time span. A higher score refers to higher costs.', '["meal_inexp", "meal_mid", "meal_mcdo"]', 'https://static.thenounproject.com/png/1826996-200.png', now()),
        (4, 44, 'Groceries', 'The score approximates the grocery costs at the destination in the selected time span. A higher score refers to higher costs.', '["bread", "eggs", "cheese", "apples", "oranges", "potato", "lettuce", "tomato", "banana", "onion", "beef", "chicken", "rice"]', 'https://static.thenounproject.com/png/5478570-200.png', now()),
        (4, 45, 'Drinks', 'The score approximates the drinking costs (including alcoholic drinks) at the destination in the selected time span. A higher score refers to higher costs.', '["water_small", "water_large", "soda", "milk", "cappuccino", "beer_dom", "beer_imp", "beer_large", "wine"]', 'https://static.thenounproject.com/png/1054446-200.png', now()),
        (4, 46, 'Transportation', 'The score approximates the local transportation costs at the destination in the selected time span. A higher score refers to higher costs.', '["transport_month", "transport_ticket", "taxi_start", "taxi_km", "taxi_hour", "gas"]', 'https://static.thenounproject.com/png/713275-200.png', now()),
        (4, 47, 'Social activities', 'The score approximates the costs regarding social activities at the destination in the selected time span. A higher score refers to higher costs.', '["gym", "tennis", "cinema"]', 'https://static.thenounproject.com/png/1945836-200.png', now()),
        (4, 48, 'Retail products', 'The score approximates the retail products costs at the destination in the selected time span. A higher score refers to higher costs.', '["jeans", "dress", "shoes_running", "shoes_business"]', 'https://static.thenounproject.com/png/1221585-200.png', now()),
        (5, 51, 'Trees', 'The score resemble the share of tree coverage at the destination.', NULL, 'https://static.thenounproject.com/png/1258519-200.png', now()),
        (5, 52, 'Shrubland', 'The score resemble the share of shrubland coverage at the destination.', NULL, 'https://static.thenounproject.com/png/1290801-200.png', now()),
        (5, 53, 'Grassland', 'The score resemble the share of grassland coverage at the destination.', NULL, 'https://static.thenounproject.com/png/2469367-200.png', now()),
        (5, 54, 'Cropland', 'The score resemble the share of cropland coverage at the destination.', NULL, 'https://static.thenounproject.com/png/5800836-200.png', now()),
        (5, 55, 'Built up', 'The score resemble the share of built up land coverage at the destination.', NULL, 'https://static.thenounproject.com/png/4393983-200.png', now()),
        (5, 56, 'Bare and sparse vegetation', 'The score resemble the share of bare and sparse vegetation coverage at the destination.', NULL, 'https://static.thenounproject.com/png/6028192-200.png', now()),
        (5, 57, 'Snow and ice', 'The score resemble the share of snow and ice coverage at the destination.', NULL, 'https://static.thenounproject.com/png/2933530-200.png', now()),
        (5, 58, 'Permanent watermarks', 'The score resemble the share of permanent watermarks coverage such as lakes, rivers, and other water features at the destination.', NULL, 'https://static.thenounproject.com/png/2446723-200.png', now()),
        (5, 59, 'Herbaceous wetland', 'The score resemble the share of herbaceous wetland coverage at the destination.', NULL, 'https://static.thenounproject.com/png/6306280-200.png', now()),
        (5, 510, 'Mangroves', 'The score resemble the share of mangroves coverage at the destination.', NULL, 'https://static.thenounproject.com/png/4841590-200.png', now()),
        (5, 511, 'Moss and lichen', 'The score resemble the share of moss and lichen coverage at the destination.', NULL, 'https://static.thenounproject.com/png/5552178-200.png', now()),
        (6, 61, 'Reachability', 'The score captures the reachability from the selected starting location to the destination at the selected time span.', NULL, 'https://static.thenounproject.com/png/2245771-200.png', now()),
        (7, 71, 'Health index', 'The health dimension measures the degree to which a reasonable quality of life is experienced by all, including material resources, shelter, basic service and connectivity. A higher score refers to better health standards and less health risks.', NULL, 'https://static.thenounproject.com/png/6497729-200.png', now())
;