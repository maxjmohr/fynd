CREATE TABLE raw_subscores_culture (
    location_id             INTEGER NOT NULL,
    category_id             INTEGER NOT NULL,
    dimension_id            INTEGER NOT NULL,
    start_date              DATE DEFAULT '2024-01-01' NOT NULL,
    end_date                DATE DEFAULT '2099-12-31' NOT NULL,
    ref_start_location_id   INTEGER DEFAULT -1 NOT NULL,
    score                   NUMERIC(10,5) NOT NULL,
    raw_value               NUMERIC,
    distance_to_median      NUMERIC NOT NULL,
    distance_to_bound       NUMERIC,
    updated_at              TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (location_id, category_id, dimension_id, start_date, end_date, ref_start_location_id),
    FOREIGN KEY (location_id) REFERENCES core_locations(location_id),
    FOREIGN KEY (category_id) REFERENCES core_categories(category_id)--,
    --FOREIGN KEY (ref_start_location_id) REFERENCES core_ref_start_locations(location_id)
);

COMMENT ON TABLE raw_subscores_culture IS 'Table stores location subscores for the culture category';

COMMENT ON COLUMN raw_subscores_culture.location_id IS 'Foreign key to the location table';
COMMENT ON COLUMN raw_subscores_culture.category_id IS 'Foreign key to the category table';
COMMENT ON COLUMN raw_subscores_culture.dimension_id IS 'Dimension of the location for the category';
COMMENT ON COLUMN raw_subscores_culture.start_date IS 'Start date of the period the score is valid for. If not filled, score is valid during entire period';
COMMENT ON COLUMN raw_subscores_culture.end_date IS 'End date of the period the score is valid for. If not filled, score is valid during entire period';
COMMENT ON COLUMN raw_subscores_culture.ref_start_location_id IS 'Foreign key to the start location table. If filled, score is valid for the location and all its children';
COMMENT ON COLUMN raw_subscores_culture.score IS 'dimension_id of the location for the dimension';
COMMENT ON COLUMN raw_subscores_culture.raw_value IS 'Raw value of the score';
COMMENT ON COLUMN raw_subscores_culture.distance_to_median IS 'Distance to the median score of the dimension';
COMMENT ON COLUMN raw_subscores_culture.distance_to_bound IS 'Distance to the upper or lower bound of the dimension. Positive if above, negative if below, NULLs if within bounds';
COMMENT ON COLUMN raw_subscores_culture.updated_at IS 'Timestamp of the last update of the score table';