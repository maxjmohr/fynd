CREATE TABLE core_categories (
    category_id     INTEGER NOT NULL,
    category_name   VARCHAR(255) NOT NULL,
    description     VARCHAR(500),
    display_order   INTEGER,
    updated_at      TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (category_id)
);

COMMENT ON TABLE core_categories IS 'Categories are used to group dimensions.';

COMMENT ON COLUMN core_categories.category_id IS 'Unique identifier of the category.';
COMMENT ON COLUMN core_categories.category_name IS 'Name of the category.';
COMMENT ON COLUMN core_categories.description IS 'Description of the category.';
COMMENT ON COLUMN core_categories.display_order IS 'Order in which to display the categories.';
COMMENT ON COLUMN core_categories.updated_at IS 'Timestamp of the last update.';
COMMENT ON COLUMN core_categories.updated_at IS 'Timestamp of the last update.';

-- Create the master data
INSERT INTO core_categories (category_id, category_name, description, display_order, updated_at)
VALUES  (0, 'General', 'General information provides a short, textual summary of the locations properties like its population or country.', 0, now()),
        (1, 'Safety', 'Safety encompasses measures and conditions that contribute to the protection of individuals, property, and well-being. It includes aspects such as crime rates, personal freedom, political stability and ecological threats', 6, now()),
        (2, 'Weather', 'Weather focuses on atmospheric conditions that influence the environment. It encompasses temperature, precipitation, humidity, and other meteorological factors that can impact daily life and activities.', 4, now()),
        (3, 'Culture', 'Culture refers to the amount of accessible places in a given location. Places can range from restaurants, tourist attractions to other entertainment venues.', 1, now()),
        (4, 'Cost', 'Costs involve the financial aspects associated with traveling to and staying in a particular location. It includes travelling and accommodation costs as well as general costs of living.', 2, now()),
        (5, 'Geography', 'Geography encompasses the physical features and characteristics of a location. It includes landforms, overall terrain and protruding landmarks that define the physical environment.', 5, now()),
        (6, 'Reachability', 'Reachability focuses on the ease of access to and from a location. It includes transportation infrastructure, connectivity, and the availability of various modes of transportation.', 3, now()),
        (7, 'Health', 'Health involves the well-being of individuals and the quality of healthcare services within a region. It encompasses factors such as suggested vaccinations, disease prevalence, and overall public health measures.', 7, now())
;