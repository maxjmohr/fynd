CREATE TABLE core_texts (
    location_id             INTEGER NOT NULL,
    category_id             INTEGER NOT NULL,
    start_date              DATE DEFAULT '2024-01-01' NOT NULL,
    end_date                DATE DEFAULT '2099-12-31' NOT NULL,
    ref_start_location_id   INTEGER DEFAULT -1 NOT NULL,
    text_general            VARCHAR NOT NULL,
    text_anomaly            VARCHAR,
    updated_at              TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (location_id, category_id, start_date, end_date, ref_start_location_id),
    FOREIGN KEY (location_id) REFERENCES core_locations(location_id),
    FOREIGN KEY (category_id) REFERENCES core_categories(category_id)--,
    --FOREIGN KEY (ref_start_location_id) REFERENCES core_ref_start_locations(location_id)
);

COMMENT ON TABLE core_texts IS 'Table stores the texts for the locations per category and period';

COMMENT ON COLUMN core_texts.location_id IS 'Foreign key to the location table';
COMMENT ON COLUMN core_texts.category_id IS 'Foreign key to the category table';
COMMENT ON COLUMN core_texts.start_date IS 'Start date of the period the score is valid for. If not filled, score is valid during entire period';
COMMENT ON COLUMN core_texts.end_date IS 'End date of the period the score is valid for. If not filled, score is valid during entire period';
COMMENT ON COLUMN core_texts.ref_start_location_id IS 'Foreign key to the start location table. If filled, score is valid for the location and all its children';
COMMENT ON COLUMN core_texts.text_general IS 'General text of the distances';
COMMENT ON COLUMN core_texts.text_anomaly IS 'Anomaly text of the distances';
COMMENT ON COLUMN core_texts.updated_at IS 'Timestamp of the last update of the score table';