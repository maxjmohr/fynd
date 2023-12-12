CREATE TABLE raw_safety_country (
    iso2                VARCHAR(2),
    iso3                VARCHAR(3) PRIMARY KEY NOT NULL,
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

COMMENT ON TABLE raw_safety_country IS 'Table stores safety data of all countries.';

COMMENT ON COLUMN raw_safety_country.iso2 IS 'ISO2 code for the country';
COMMENT ON COLUMN raw_safety_country.iso3 IS 'ISO3 code for the country';
COMMENT ON COLUMN raw_safety_country.country_name IS 'Name the country';
COMMENT ON COLUMN raw_safety_country.political_stability IS 'Political stability index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety_country.rule_of_law IS 'Rule of Law index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety_country.personal_freedom IS 'Personal Freedom index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety_country.crime_rate IS 'Crime rate index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety_country.peace_index IS 'Peace index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety_country.terrorism_index IS 'Terrorism index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety_country.ecological_threat IS 'Ecological threat index for the country, scored 0-10';
COMMENT ON COLUMN raw_safety_country.updated_at IS 'Timestamp of the last update of the record';