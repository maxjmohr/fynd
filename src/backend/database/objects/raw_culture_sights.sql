CREATE TABLE raw_culture_sights (
    location_id                 INTEGER NOT NULL,
    sight_rank                  INTEGER NOT NULL,
    sight                       VARCHAR(100),
    updated_at                  TIMESTAMP,
    PRIMARY KEY (location_id, sight_rank),
    FOREIGN KEY (location_id) REFERENCES core_locations(location_id)
);

COMMENT ON TABLE raw_culture_sights IS 'Table stores cultural sights to be displayed on location pages.';

COMMENT ON COLUMN raw_culture_sights.location_id IS 'Unique identifier for the location';
COMMENT ON COLUMN raw_culture_sights.sight_rank IS 'Unique identifier for the rank of a cultural sight for a location';
COMMENT ON COLUMN raw_culture_sights.sight IS 'Name of the cultural sight for this location';
COMMENT ON COLUMN raw_culture_sights.updated_at IS 'Timestamp of the last update of the record';