CREATE TABLE raw_places (
    location_id         INTEGER NOT NULL,
    place_name          VARCHAR(10000),
    place_category      VARCHAR(10000),
    lat                 NUMERIC(10,7),
    lon                 NUMERIC(10,7),
    vegetarian          INTEGER,
    vegan               INTEGER,
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (location_id, place_name, place_category),
    FOREIGN KEY (location_id) REFERENCES core_locations(location_id)
);

COMMENT ON TABLE raw_places IS 'Table stores all places of interest in a location.';

COMMENT ON COLUMN raw_places.location_id IS 'Unique identifier for the location';
COMMENT ON COLUMN raw_places.place_name IS 'Name of the place';
COMMENT ON COLUMN raw_places.place_category IS 'Categories of the place';
COMMENT ON COLUMN raw_places.lat IS 'Latitude of the place';
COMMENT ON COLUMN raw_places.lon IS 'Longitude of the place';
COMMENT ON COLUMN raw_places.vegetarian IS '1 if vegetarian';
COMMENT ON COLUMN raw_places.vegan IS '1 if vegan';