CREATE TABLE raw_travel_warnings (
    country_code        VARCHAR(2) PRIMARY KEY NOT NULL,
    country_name        VARCHAR(64),
    warning_text        TEXT,
    link                TEXT,
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01')
);

COMMENT ON TABLE raw_travel_warnings IS 'Table stores safety data of all countries.';

COMMENT ON COLUMN raw_travel_warnings.country_code IS 'ISO 3166-1 alpha-2 code for the country';
COMMENT ON COLUMN raw_travel_warnings.country_name IS 'Name the country';
COMMENT ON COLUMN raw_travel_warnings.warning_text IS 'Travel warning text to be displayed on the location page.';
COMMENT ON COLUMN raw_travel_warnings.link IS 'Link to the German foreign office page for the specific country with more information on the warning.';
COMMENT ON COLUMN raw_travel_warnings.updated_at IS 'Timestamp of the last update of the record';