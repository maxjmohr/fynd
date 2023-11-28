DROP TABLE IF EXISTS CORE_LOCATIONS;

CREATE TABLE CORE_LOCATIONS (
    LOCATION_ID         SERIAL PRIMARY KEY NOT NULL,
    CITY                VARCHAR(255) NOT NULL,
    DISTRICT            VARCHAR(255),
    STATE               VARCHAR(255),
    COUNTRY             VARCHAR(255) NOT NULL,
    ADRESS_TYPE         VARCHAR(255),
    LAT                 NUMERIC(10,7) NOT NULL,
    LON                 NUMERIC(10,7) NOT NULL,
    RADIUS_KM           NUMERIC(4,0),
    BOX_BOTTOM_LEFT_LAT NUMERIC(10,7),
    BOX_BOTTOM_LEFT_LON NUMERIC(10,7),
    BOX_TOP_RIGHT_LAT   NUMERIC(10,7),
    BOX_TOP_RIGHT_LON   NUMERIC(10,7),
    UPDATED_AT          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE CORE_LOCATIONS IS 'Table stores geographical master data of all locations.';

COMMENT ON COLUMN CORE_LOCATIONS.LOCATION_ID IS 'Unique identifier for the location';
COMMENT ON COLUMN CORE_LOCATIONS.CITY IS 'City name';
COMMENT ON COLUMN CORE_LOCATIONS.DISTRICT IS 'District name';
COMMENT ON COLUMN CORE_LOCATIONS.STATE IS 'State name';
COMMENT ON COLUMN CORE_LOCATIONS.COUNTRY IS 'Country name';
COMMENT ON COLUMN CORE_LOCATIONS.ADRESS_TYPE IS 'Type of address';
COMMENT ON COLUMN CORE_LOCATIONS.LAT IS 'Latitude of the location';
COMMENT ON COLUMN CORE_LOCATIONS.LON IS 'Longitude of the location';
COMMENT ON COLUMN CORE_LOCATIONS.RADIUS_KM IS 'Radius of the location in kilometers to include the entire location geographically';
COMMENT ON COLUMN CORE_LOCATIONS.BOX_BOTTOM_LEFT_LAT IS 'Latitude of the bottom left corner of the bounding box to include the entire location geographically';
COMMENT ON COLUMN CORE_LOCATIONS.BOX_BOTTOM_LEFT_LON IS 'Longitude of the bottom left corner of the bounding box to include the entire location geographically';
COMMENT ON COLUMN CORE_LOCATIONS.BOX_TOP_RIGHT_LAT IS 'Latitude of the top right corner of the bounding box to include the entire location geographically';
COMMENT ON COLUMN CORE_LOCATIONS.BOX_TOP_RIGHT_LON IS 'Longitude of the top right corner of the bounding box to include the entire location geographically';
COMMENT ON COLUMN CORE_LOCATIONS.UPDATED_AT IS 'Timestamp of the last update of the record';