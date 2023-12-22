CREATE TABLE core_dimensions (
    dimension_id        INTEGER NOT NULL,
    dimension           VARCHAR(255) NOT NULL,
    description         VARCHAR(255),
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (dimension_id)
);

COMMENT ON TABLE core_dimensions IS 'Table stores dimensions and subcategories of the dimensions.';

COMMENT ON COLUMN core_dimensions.dimension_id IS 'Primary key of the dimension table';
COMMENT ON COLUMN core_dimensions.dimension IS 'Dimension of the score';
COMMENT ON COLUMN core_dimensions.description IS 'Description of the dimension';
COMMENT ON COLUMN core_dimensions.updated_at IS 'Timestamp of the last update of the dimension table';

-- Create the master data
INSERT INTO core_dimensions (dimension_id, dimension, description, updated_at)
VALUES (1, 'safety', 'Safety', now()),
       (2, 'weather', 'Weather', now()),
       (3, 'culture', 'Culture', now()),
       (4, 'cost', 'Cost dimension includes travel costs, accommodation costs and cost of living.', now()),
       (5, 'geography', 'Geography', now());