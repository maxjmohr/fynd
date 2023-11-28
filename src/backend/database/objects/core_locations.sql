DROP TABLE IF EXISTS core_locations;

CREATE TABLE core_locations (
    location_id         NUMERIC(9,0) PRIMARY KEY NOT NULL,
    city                VARCHAR(255) NOT NULL,
    district            VARCHAR(255),
    state               VARCHAR(255),
    country             VARCHAR(255) NOT NULL,
    adress_type         VARCHAR(255),
    lat                 NUMERIC(10,7) NOT NULL,
    lon                 NUMERIC(10,7) NOT NULL,
    radius_km           NUMERIC(4,0),
    box_bottom_left_lat NUMERIC(10,7),
    box_bottom_left_lon NUMERIC(10,7),
    box_top_right_lat   NUMERIC(10,7),
    box_top_right_lon   NUMERIC(10,7),
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01')
);

COMMENT ON TABLE core_locations IS 'Table stores geographical master data of all locations.';

COMMENT ON COLUMN core_locations.location_id IS 'Unique identifier for the location';
COMMENT ON COLUMN core_locations.city IS 'City name';
COMMENT ON COLUMN core_locations.district IS 'District name';
COMMENT ON COLUMN core_locations.state IS 'State name';
COMMENT ON COLUMN core_locations.country IS 'Country name';
COMMENT ON COLUMN core_locations.adress_type IS 'Type of address';
COMMENT ON COLUMN core_locations.lat IS 'Latitude of the location';
COMMENT ON COLUMN core_locations.lon IS 'Longitude of the location';
COMMENT ON COLUMN core_locations.radius_km IS 'Radius of the location in kilometers to include the entire location geographically';
COMMENT ON COLUMN core_locations.box_bottom_left_lat IS 'Latitude of the bottom left corner of the bounding box to include the entire location geographically';
COMMENT ON COLUMN core_locations.box_bottom_left_lon IS 'Longitude of the bottom left corner of the bounding box to include the entire location geographically';
COMMENT ON COLUMN core_locations.box_top_right_lat IS 'Latitude of the top right corner of the bounding box to include the entire location geographically';
COMMENT ON COLUMN core_locations.box_top_right_lon IS 'Longitude of the top right corner of the bounding box to include the entire location geographically';
COMMENT ON COLUMN core_locations.updated_at IS 'Timestamp of the last update of the record';