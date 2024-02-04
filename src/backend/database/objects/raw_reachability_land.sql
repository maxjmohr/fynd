DROP TABLE IF EXISTS raw_reachability_land;

CREATE TABLE raw_reachability_land (
    location_id INTEGER NOT NULL,
    reference_loc_id INTEGER NOT NULL,
    arr_city VARCHAR(255),
    dep_city VARCHAR(255),
    car_distance NUMERIC(15, 2),
    car_duration NUMERIC(15, 2),
    car_polyline VARCHAR(MAX),
    pub_trans_distance NUMERIC(15, 2),
    pub_trans_duration NUMERIC(15, 2),
    pub_trans_polyline VARCHAR(MAX),
    pub_trans_total_transfers INTEGER,

    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01')
    );

ALTER TABLE raw_accommodation ADD PRIMARY KEY (location_id, reference_loc_id);
        
COMMENT ON TABLE raw_reachability_land IS 'Table stores land reachability data for a given destination and a reference start location.';

COMMENT ON COLUMN raw_reachability_land.location_id IS 'Unique identifier for the destination location';
COMMENT ON COLUMN raw_reachability_land.reference_loc_id IS 'Unique identifier for the reference start location';
COMMENT ON COLUMN raw_reachability_land.car_distance IS 'Distance in meters for the car route';
COMMENT ON COLUMN raw_reachability_land.car_duration IS 'Duration in seconds for the car route';
COMMENT ON COLUMN raw_reachability_land.car_polyline IS 'Polyline for the car route';
COMMENT ON COLUMN raw_reachability_land.pub_trans_distance IS 'Distance in meters for the public transport route';
COMMENT ON COLUMN raw_reachability_land.pub_trans_duration IS 'Duration in seconds for the public transport route';
COMMENT ON COLUMN raw_reachability_land.pub_trans_polyline IS 'Polyline for the public transport route';
COMMENT ON COLUMN raw_reachability_land.pub_trans_total_transfers IS 'Total number of transfers for the public transport route';