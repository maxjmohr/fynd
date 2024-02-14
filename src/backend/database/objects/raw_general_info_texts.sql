CREATE TABLE raw_general_info_texts (
    location_id                 INTEGER NOT NULL,
    category_id                 INTEGER NOT NULL,
    text                        TEXT,
    updated_at                  TIMESTAMP,
    PRIMARY KEY (location_id, category_id),
    FOREIGN KEY (location_id) REFERENCES core_locations(location_id),
    FOREIGN KEY (category_id) REFERENCES core_categories(category_id)
);

COMMENT ON TABLE raw_general_info_texts IS 'Table stores texts containing general information to be displayed on location pages.';

COMMENT ON COLUMN raw_general_info_texts.location_id IS 'Unique identifier for the location';
COMMENT ON COLUMN raw_general_info_texts.category_id IS 'Unique identifier for the category';
COMMENT ON COLUMN raw_general_info_texts.text IS 'General information text for this location and this category';
COMMENT ON COLUMN raw_general_info_texts.updated_at IS 'Timestamp of the last update of the record';