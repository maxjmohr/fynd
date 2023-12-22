CREATE TABLE core_scores (
    location_id    INTEGER NOT NULL,
    dimension_id   INTEGER NOT NULL,
    subcategory_id INTEGER,
    score          NUMERIC(10,5),
    updated_at     TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (location_id, dimension_id, subcategory_id),
    FOREIGN KEY (location_id) REFERENCES core_locations(location_id),
    FOREIGN KEY (dimension_id) REFERENCES core_dimensions(dimension_id),
    FOREIGN KEY (subcategory_id) REFERENCES core_subcategories(subcategory_id)
);

COMMENT ON TABLE core_scores IS 'Table stores location scores of each dimension for each location.';

COMMENT ON COLUMN core_scores.location_id IS 'Foreign key to the location table';
COMMENT ON COLUMN core_scores.dimension_id IS 'Foreign key to the dimension table';
COMMENT ON COLUMN core_scores.subcategory_id IS 'Foreign key to the subcategory table';
COMMENT ON COLUMN core_scores.score IS 'Score of the location for the dimension';
COMMENT ON COLUMN core_scores.updated_at IS 'Timestamp of the last update of the score table';