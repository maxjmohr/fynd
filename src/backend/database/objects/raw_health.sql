CREATE TABLE raw_health_country (
    iso3                VARCHAR(3) PRIMARY KEY NOT NULL,
    country_name        VARCHAR(64),
    safety              TEXT,
    nature_climate      TEXT,
    travel              TEXT,
    entry               TEXT,
    health              TEXT,
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01')
);

COMMENT ON TABLE raw_health_country IS 'Table stores health data and other textual information of all countries gathered from the website of the German foreign ministry.';

COMMENT ON COLUMN raw_health_country.iso3 IS 'ISO3 code for the country';
COMMENT ON COLUMN raw_health_country.country_name IS 'Name the country';
COMMENT ON COLUMN raw_health_country.safety IS 'Information on terrorism, criminality and other risk factors in the country';
COMMENT ON COLUMN raw_health_country.nature_climate IS 'Information on the countries climate and natural disasters';
COMMENT ON COLUMN raw_health_country.travel IS 'Information on local travel conditions like infrastructure, payment options and personal rights';
COMMENT ON COLUMN raw_health_country.entry IS 'Information on entry conditions for the country';
COMMENT ON COLUMN raw_health_country.health IS 'Information on diseases and other health risks in the country as well as availability of medical services';
COMMENT ON COLUMN raw_safety_country.updated_at IS 'Timestamp of the last update of the record';