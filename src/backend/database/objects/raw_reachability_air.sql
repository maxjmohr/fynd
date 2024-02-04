DROP TABLE IF EXISTS raw_reachability_air;

CREATE TABLE raw_reachability_air (
    orig_iata VARCHAR(5) NOT NULL,
    dest_iata VARCHAR(5) NOT NULL,
    dep_date DATE NOT NULL,
    total_flights INTEGER,
    avg_price NUMERIC(15, 2),
    min_price NUMERIC(15, 2),
    max_price NUMERIC(15, 2),
    avg_duration NUMERIC(15, 2),
    min_duration NUMERIC(15, 2),
    max_duration NUMERIC(15, 2),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01')
    );

ALTER TABLE raw_accommodation ADD PRIMARY KEY (dest_iata, orig_iata, dep_date);
        
COMMENT ON TABLE raw_reachability_air IS 'Table stores air (flight) reachability data for a given destination and a reference start location.';

COMMENT ON COLUMN raw_reachability_air.location_id IS 'Unique identifier for the destination location';
COMMENT ON COLUMN raw_reachability_air.reference_loc_id IS 'Unique identifier for the reference start location';
COMMENT ON COLUMN raw_reachability_air.dep_date IS 'Departure date';
COMMENT ON COLUMN raw_reachability_air.total_flights IS 'Total number of flights';
COMMENT ON COLUMN raw_reachability_air.avg_price IS 'Average price of the flights';
COMMENT ON COLUMN raw_reachability_air.min_price IS 'Minimum price of the flights';
COMMENT ON COLUMN raw_reachability_air.max_price IS 'Maximum price of the flights';
COMMENT ON COLUMN raw_reachability_air.avg_duration IS 'Average duration of the flights';
COMMENT ON COLUMN raw_reachability_air.min_duration IS 'Minimum duration of the flights';
COMMENT ON COLUMN raw_reachability_air.max_duration IS 'Maximum duration of the flights';
COMMENT ON COLUMN raw_reachability_air.updated_at IS 'Timestamp of the last update of the record';