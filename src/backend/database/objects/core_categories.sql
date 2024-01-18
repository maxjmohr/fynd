CREATE TABLE core_categories (
    category_id     INTEGER NOT NULL,
    category        VARCHAR(255) NOT NULL,
    description     VARCHAR(500),
    updated_at      TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (category_id)
);

COMMENT ON TABLE core_categories IS 'Categories are used to group dimensions.';

COMMENT ON COLUMN core_categories.category_id IS 'Unique identifier of the category.';
COMMENT ON COLUMN core_categories.category IS 'Name of the category.';
COMMENT ON COLUMN core_categories.description IS 'Description of the category.';
COMMENT ON COLUMN core_categories.updated_at IS 'Timestamp of the last update.';
COMMENT ON COLUMN core_categories.updated_at IS 'Timestamp of the last update.';

-- Create the master data
INSERT INTO core_categories (category_id, category, description, updated_at)
VALUES (1, 'safety', 'Safety encompasses measures and conditions that contribute to the protection of individuals, property, and well-being. It includes aspects such as crime rates, personal freedom, political stability and ecological threats', now()),
       (2, 'weather', 'Weather focuses on atmospheric conditions that influence the environment. It encompasses temperature, precipitation, humidity, and other meteorological factors that can impact daily life and activities.', now()),
       (3, 'culture', 'Culture refers to the offered ', now()),
       (4, 'cost', 'Costs involve the financial aspects associated with traveling to and staying in a particular location. It includes travelling and accommodation costs as well as general costs of living.', now()),
       (5, 'geography', 'Geography encompasses the physical features and characteristics of a location. It includes landforms, overall terrain and protruding landmarks that define the physical environment.', now()),
       (6, 'reachability', 'Reachability focuses on the ease of access to and from a location. It includes transportation infrastructure, connectivity, and the availability of various modes of transportation.', now()),
       (7, 'health', 'Health involves the well-being of individuals and the quality of healthcare services within a region. It encompasses factors such as suggested vaccinations, disease prevalence, and overall public health measures.', now())
;