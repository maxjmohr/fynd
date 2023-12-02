DROP TABLE IF EXISTS raw_culture;

CREATE TABLE raw_culture (
    fsq_id              VARCHAR(255) PRIMARY KEY NOT NULL,
    categories          VARCHAR(10000),
    distance            NUMERIC(10,5),
    location            VARCHAR(1000),
    name                VARCHAR(255),
    popularity          NUMERIC(15,10),
    rating              NUMERIC(15,10),
    stats               VARCHAR(1000),
    description         VARCHAR(1000),
    price               NUMERIC(10,5),
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01')
);

COMMENT ON TABLE raw_culture IS 'Table stores data for places covering many cultural aspects of all cities.';

COMMENT ON COLUMN raw_culture.fsq_id IS 'Unique identifier for the culture site';
COMMENT ON COLUMN raw_culture.categories IS 'Dictionary of cultural categories this culture site belongs to';
COMMENT ON COLUMN raw_culture.distance IS 'Distances of the culture site from the city center';
COMMENT ON COLUMN raw_culture.location IS 'Address of the culture site';
COMMENT ON COLUMN raw_culture.name IS 'Name of the culture site';
COMMENT ON COLUMN raw_culture.popularity IS 'Relative popularity of the culture site';
COMMENT ON COLUMN raw_culture.rating IS 'Rating of the culture site';
COMMENT ON COLUMN raw_culture.stats IS 'Statistics concerning the culture site';
COMMENT ON COLUMN raw_culture.description IS 'More exact description of the culture site';
COMMENT ON COLUMN raw_culture.price IS 'Price associated with visiting the culture site';
COMMENT ON COLUMN raw_culture.updated_at IS 'Timestamp of the last update of the record';