CREATE TABLE raw_health_numeric (
    country_name        VARCHAR(64) PRIMARY KEY NOT NULL,
    health_score        NUMERIC(6,3),
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01')
);

COMMENT ON TABLE raw_health_numeric IS 'Table stores health score from the Legatum Prosperity Index for all available countries.';

COMMENT ON COLUMN raw_health_numeric.country_name IS 'Name of the country';
COMMENT ON COLUMN raw_health_numeric.health_score IS 'Health score in the country based on factors such as availability of medical services and medical risk factors like prevalent diseases';
COMMENT ON COLUMN raw_safety_numeric.updated_at IS 'Timestamp of the last update of the record';