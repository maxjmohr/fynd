DROP TABLE IF EXISTS raw_reachability_land;

CREATE TABLE raw_reachability_land (
    loc_id INTEGER NOT NULL,
    ref_id INTEGER NOT NULL,
    arr_city VARCHAR(255),
    dep_city VARCHAR(255),
    car_distance NUMERIC(15, 2),
    car_duration NUMERIC(15, 2),
    car_polyline TEXT,
    car_geojson TEXT,
    pt_distance NUMERIC(15, 2),
    pt_duration NUMERIC(15, 2),
    pt_polyline TEXT,
    pt_geojson TEXT,
    pt_total_transfers INTEGER,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    FOREIGN KEY (ref_id) REFERENCES core_ref_start_locations(location_id),
    FOREIGN KEY (loc_id) REFERENCES core_locations(location_id)
    );

ALTER TABLE raw_reachability_land ADD PRIMARY KEY (loc_id, ref_id);
        
COMMENT ON TABLE raw_reachability_land IS 'Table stores land reachability data for a given destination and a reference start location.';

COMMENT ON COLUMN raw_reachability_land.loc_id IS 'Unique identifier for the destination location';
COMMENT ON COLUMN raw_reachability_land.ref_id IS 'Unique identifier for the reference start location';
COMMENT ON COLUMN raw_reachability_land.arr_city IS 'Arrival city for the route';
COMMENT ON COLUMN raw_reachability_land.dep_city IS 'Departure city for the route';
COMMENT ON COLUMN raw_reachability_land.car_distance IS 'Distance in meters for the car route';
COMMENT ON COLUMN raw_reachability_land.car_duration IS 'Duration in seconds for the car route';
COMMENT ON COLUMN raw_reachability_land.car_polyline IS 'Polyline for the car route';
COMMENT ON COLUMN raw_reachability_land.pt_distance IS 'Distance in meters for the public transport route';
COMMENT ON COLUMN raw_reachability_land.pt_duration IS 'Duration in seconds for the public transport route';
COMMENT ON COLUMN raw_reachability_land.pt_polyline IS 'Polyline for the public transport route';
COMMENT ON COLUMN raw_reachability_land.pt_total_transfers IS 'Total number of transfers for the public transport route';
COMMENT ON COLUMN raw_reachability_land.updated_at IS 'Timestamp of the last update of the record';
COMMENT ON COLUMN raw_reachability_land.car_geojson IS 'GeoJSON of the car route';
COMMENT ON COLUMN raw_reachability_land.pt_geojson IS 'GeoJSON of the public transport route';