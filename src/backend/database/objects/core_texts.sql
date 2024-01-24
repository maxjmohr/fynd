CREATE TABLE core_texts (
    location_id                 INTEGER NOT NULL,
    category_id                 INTEGER NOT NULL,
    start_date                  DATE,
    end_date	                DATE,
    reference_start_location    VARCHAR(100),
    text                        TEXT,
    updated_at                  TIMESTAMP,
    PRIMARY KEY (location_id, category_id),
    FOREIGN KEY (location_id) REFERENCES core_locations(location_id),
    FOREIGN KEY (category_id) REFERENCES core_categories(category_id)
);

COMMENT ON TABLE core_texts IS 'Table stores texts for all cateogries to be displayed on location pages.';

COMMENT ON COLUMN core_texts.location_id IS 'Unique identifier for the location';
COMMENT ON COLUMN core_texts.category_id IS 'Unique identifier for the category';
COMMENT ON COLUMN core_texts.start_date IS 'Date from which this text is valid';
COMMENT ON COLUMN core_texts.end_date IS 'Date until which this text is valid';
COMMENT ON COLUMN core_texts.reference_start_location IS 'Location which is used as a proxy start location for the starting point of the user';
COMMENT ON COLUMN core_texts.text IS 'Text for this location and this category';
COMMENT ON COLUMN core_texts.updated_at IS 'Timestamp of the last update of the record';