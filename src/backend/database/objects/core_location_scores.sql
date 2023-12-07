CREATE TABLE core_location_scores (
    location_id    INTEGER,
    city           VARCHAR(255),
    country        VARCHAR(255),
    dimension      VARCHAR(255) NOT NULL,
    subcategory    VARCHAR(255),
    scores         NUMERIC(10,5),
    updated_at     TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (location_id, dimension, subcategory),
    FOREIGN KEY (location_id) REFERENCES core_locations(location_id)
);

COMMENT ON TABLE core_location_scores IS 'Table stores location scores of each dimension for each location.';

COMMENT ON COLUMN core_location_scores.location_id IS 'Foreign key to the location table';
COMMENT ON COLUMN core_location_scores.city IS 'City of the weather data point';
COMMENT ON COLUMN core_location_scores.country IS 'Country of the weather data point';
COMMENT ON COLUMN core_location_scores.dimension IS 'Dimension of the score';
COMMENT ON COLUMN core_location_scores.subcategory IS 'Subcategory of the dimension';
COMMENT ON COLUMN core_location_scores.scores IS 'Score of the dimension (and subcategory)';