CREATE TABLE raw_geography_coverage (
    location_id             INTEGER NOT NULL,
    tree_cover              NUMERIC(10,9),
    shrubland               NUMERIC(10,9),
    grassland               NUMERIC(10,9),
    cropland                NUMERIC(10,9),
    built_up                NUMERIC(10,9),
    bare_sparse_vegetation  NUMERIC(10,9),
    snow_ice                NUMERIC(10,9),
    permanent_water         NUMERIC(10,9),
    herbaceous_wetland      NUMERIC(10,9),
    mangroves               NUMERIC(10,9),
    moss_lichen             NUMERIC(10,9),
    updated_at              TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (location_id),
    FOREIGN KEY (location_id) REFERENCES core_locations(location_id)
);

COMMENT ON TABLE raw_geography_coverage IS 'Table stores the current land coverage shares by ESA Worldcover v10 100m for each location.';

COMMENT ON COLUMN raw_geography_coverage.location_id IS 'Foreign key to the location table';
COMMENT ON COLUMN raw_geography_coverage.tree_cover IS 'Share of tree cover';
COMMENT ON COLUMN raw_geography_coverage.shrubland IS 'Share of shrubland';
COMMENT ON COLUMN raw_geography_coverage.grassland IS 'Share of grassland';
COMMENT ON COLUMN raw_geography_coverage.cropland IS 'Share of cropland';
COMMENT ON COLUMN raw_geography_coverage.built_up IS 'Share of built up land';
COMMENT ON COLUMN raw_geography_coverage.bare_sparse_vegetation IS 'Share of bare sparse vegetation';
COMMENT ON COLUMN raw_geography_coverage.snow_ice IS 'Share of snow and ice';
COMMENT ON COLUMN raw_geography_coverage.permanent_water IS 'Share of permanent water bodies';
COMMENT ON COLUMN raw_geography_coverage.herbaceous_wetland IS 'Share of herbaceous wetland';
COMMENT ON COLUMN raw_geography_coverage.mangroves IS 'Share of mangroves';
COMMENT ON COLUMN raw_geography_coverage.moss_lichen IS 'Share of moss and lichen';
COMMENT ON COLUMN raw_geography_coverage.updated_at IS 'Timestamp of the last update of the record';