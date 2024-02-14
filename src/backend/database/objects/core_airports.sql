CREATE TABLE core_airports (
    iata_code       VARCHAR(3) NOT NULL,
    airport_name    VARCHAR(255),
    city            VARCHAR(255),
    country         VARCHAR(255),
    lat             NUMERIC(10,7) NOT NULL,
    lon             NUMERIC(10,7) NOT NULL,
    passenger_count VARCHAR(15),
    updated_at      TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (iata_code)
);

COMMENT ON TABLE core_airports IS 'Table stores master data of all airports.';

COMMENT ON COLUMN core_airports.iata_code IS 'Unique identifier for the airport';
COMMENT ON COLUMN core_airports.airport_name IS 'Airport name';
COMMENT ON COLUMN core_airports.city IS 'City name';
COMMENT ON COLUMN core_airports.country IS 'Country name';
COMMENT ON COLUMN core_airports.lat IS 'Latitude of the airport';
COMMENT ON COLUMN core_airports.lon IS 'Longitude of the airport';
COMMENT ON COLUMN core_airports.passenger_count IS 'Number of passengers';
COMMENT ON COLUMN core_airports.updated_at IS 'Timestamp of the last update of the record';