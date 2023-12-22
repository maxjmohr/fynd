CREATE TABLE core_subcategories (
    dimension_id        INTEGER NOT NULL,
    subcategory_id      INTEGER NOT NULL,
    subcategory         VARCHAR(255),
    description         VARCHAR(255),
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (subcategory_id),
    FOREIGN KEY (dimension_id) REFERENCES core_dimensions(dimension_id)
);

COMMENT ON TABLE core_subcategories IS 'Table stores dimensions and subcategories of the dimensions.';

COMMENT ON COLUMN core_subcategories.dimension_id IS 'Foreign key of the dimension table';
COMMENT ON COLUMN core_subcategories.subcategory_id IS 'Primary key of the subcategory table';
COMMENT ON COLUMN core_subcategories.subcategory IS 'Subcategory of the dimension';
COMMENT ON COLUMN core_subcategories.description IS 'Description of the subcategory';
COMMENT ON COLUMN core_subcategories.updated_at IS 'Timestamp of the last update of the subcategory table';

-- Create subcategories for cost
INSERT INTO core_subcategories (dimension_id, subcategory_id, subcategory, description, updated_at)
VALUES (4, 41, 'travel', 'Travel costs as part of cost dimension', now()),
       (4, 42, 'accommodation', 'Accommodation costs as part of cost dimension', now()),
       (4, 43, 'cost_of_living', 'Cost of living as part of cost dimension', now());