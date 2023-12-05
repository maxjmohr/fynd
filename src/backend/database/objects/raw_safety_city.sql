DROP TABLE IF EXISTS raw_safety_city;

CREATE TABLE raw_safety_city (
    city_name           VARCHAR(64) PRIMARY KEY NOT NULL,
    safety              NUMERIC(8,6),
    healthcare          NUMERIC(8,6),
    environmental_qual  NUMERIC(8,6),
    tolerance           NUMERIC(8,6),
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01')
);

COMMENT ON TABLE raw_safety_city IS 'Table stores safety data of all available cites.';

COMMENT ON COLUMN raw_safety_city.city_name IS 'Name of the city';
COMMENT ON COLUMN raw_safety_city.safety IS 'Safety score for the city';
COMMENT ON COLUMN raw_safety_city.healthcare IS 'Healthcare availability and quality score for the city';
COMMENT ON COLUMN raw_safety_city.environmental_qual IS 'Environmental quality score for the city';
COMMENT ON COLUMN raw_safety_city.tolerance IS 'Tolerance score for the city';
COMMENT ON COLUMN raw_safety_city.updated_at IS 'Timestamp of the last update of the record';