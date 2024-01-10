CREATE TABLE core_locations (
    location_id         INTEGER NOT NULL,
    city                VARCHAR(255) NOT NULL,
    county              VARCHAR(255),
    state               VARCHAR(255),
    country             VARCHAR(255) NOT NULL,
    country_code        VARCHAR(2),
    address_type        VARCHAR(255),
    population          INTEGER,
    lat                 NUMERIC(10,7) NOT NULL,
    lon                 NUMERIC(10,7) NOT NULL,
    radius_km           INTEGER,
    box_bottom_left_lat NUMERIC(10,7),
    box_bottom_left_lon NUMERIC(10,7),
    box_top_right_lat   NUMERIC(10,7),
    box_top_right_lon   NUMERIC(10,7),
    geojson             JSONB,
    updated_at          TIMESTAMP,
    PRIMARY KEY (location_id)
);

COMMENT ON TABLE core_locations IS 'Table stores geographical master data of all locations.';

COMMENT ON COLUMN core_locations.location_id IS 'Unique identifier for the location';
COMMENT ON COLUMN core_locations.city IS 'City name';
COMMENT ON COLUMN core_locations.county IS 'County name';
COMMENT ON COLUMN core_locations.state IS 'State name';
COMMENT ON COLUMN core_locations.country IS 'Country name';
COMMENT ON COLUMN core_locations.country_code IS 'Country code';
COMMENT ON COLUMN core_locations.address_type IS 'Type of address';
COMMENT ON COLUMN core_locations.population IS 'Population of the location (might not be up-to-date)';
COMMENT ON COLUMN core_locations.lat IS 'Latitude of the location';
COMMENT ON COLUMN core_locations.lon IS 'Longitude of the location';
COMMENT ON COLUMN core_locations.radius_km IS 'Radius of the location in kilometers to include the entire location geographically';
COMMENT ON COLUMN core_locations.box_bottom_left_lat IS 'Latitude of the bottom left corner of the bounding box to include the entire location geographically';
COMMENT ON COLUMN core_locations.box_bottom_left_lon IS 'Longitude of the bottom left corner of the bounding box to include the entire location geographically';
COMMENT ON COLUMN core_locations.box_top_right_lat IS 'Latitude of the top right corner of the bounding box to include the entire location geographically';
COMMENT ON COLUMN core_locations.box_top_right_lon IS 'Longitude of the top right corner of the bounding box to include the entire location geographically';
COMMENT ON COLUMN core_locations.geojson IS 'GeoJSON representation of the location';
COMMENT ON COLUMN core_locations.updated_at IS 'Timestamp of the last update of the record';