CREATE TABLE core_categories (
    category_id     INTEGER NOT NULL,
    category        VARCHAR(255) NOT NULL,
    description     VARCHAR(255),
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
VALUES (1, 'safety', 'Safety', now()),
       (2, 'weather', 'Weather', now()),
       (3, 'culture', 'Culture', now()),
       (4, 'cost', 'Cost dimension includes travel costs, accommodation costs and cost of living.', now()),
       (5, 'geography', 'Geography', now());