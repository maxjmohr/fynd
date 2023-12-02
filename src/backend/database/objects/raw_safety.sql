DROP TABLE IF EXISTS raw_safety;

CREATE TABLE raw_safety (
    country_id          INTEGER PRIMARY KEY NOT NULL,
    iso2                VARCHAR(2),
    iso3                VARCHAR(3),
    country_name        VARCHAR(32),
    political_stability NUMERIC(7,5),
    rule_of_law         NUMERIC(7,5),
    personal_freedom    NUMERIC(7,5),
    crime_rate          NUMERIC(7,5),
    peace_index         NUMERIC(7,5),
    terrorism_index     NUMERIC(7,5),
    ecological_threat   NUMERIC(7,5),
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01')
);

COMMENT ON TABLE raw_safety IS 'Table stores safety data of all countries.';

COMMENT ON COLUMN raw_safety.country_id IS 'Unique identifier for the country';
COMMENT ON COLUMN raw_safety.iso2 IS 'ISO2 code for the country';
COMMENT ON COLUMN raw_safety.iso3 IS 'ISO3 code for the country';
COMMENT ON COLUMN raw_safety.country_name IS 'Name the country';
COMMENT ON COLUMN raw_safety.political_stability IS 'Political stability index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety.rule_of_law IS 'Rule of Law index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety.personal_freedom IS 'Personal Freedom index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety.crime_rate IS 'Crime rate index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety.peace_index IS 'Peace index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety.terrorism_index IS 'Terrorism index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety.ecological_threat IS 'Ecological threat index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety.updated_at IS 'Timestamp of the last update of the record';