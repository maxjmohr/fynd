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

-- Create subcategories for cost
INSERT INTO core_dimensions (category_id, dimension_id, dimension, description, updated_at)
VALUES (4, 41, 'travel', 'Travel costs as part of cost dimension', now()),
       (4, 42, 'accommodation', 'Accommodation costs as part of cost dimension', now()),
       (4, 43, 'cost_of_living', 'Cost of living as part of cost dimension', now());