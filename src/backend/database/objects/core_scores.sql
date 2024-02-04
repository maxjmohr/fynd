CREATE TABLE core_scores (
    location_id         INTEGER NOT NULL,
    category_id         INTEGER NOT NULL,
    dimension_id        INTEGER NOT NULL,
    start_date          DATE DEFAULT '2024-01-01' NOT NULL,
    end_date            DATE DEFAULT '2099-12-31' NOT NULL,
    score               NUMERIC(10,5) NOT NULL,
    raw_value_formatted VARCHAR(255),
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (location_id, category_id, dimension_id, start_date, end_date),
    FOREIGN KEY (location_id) REFERENCES core_locations(location_id),
    FOREIGN KEY (category_id) REFERENCES core_categories(category_id),
    FOREIGN KEY (dimension_id) REFERENCES core_dimensions(dimension_id)
);

COMMENT ON TABLE core_scores IS 'Table stores location scores of each dimension for each location.';

COMMENT ON COLUMN core_scores.location_id IS 'Foreign key to the location table';
COMMENT ON COLUMN core_scores.category_id IS 'Foreign key to the category table';
COMMENT ON COLUMN core_scores.dimension_id IS 'Foreign key to the dimension table';
COMMENT ON COLUMN core_scores.start_date IS 'Start date of the period the score is valid for. If not filled, score is valid during entire period';
COMMENT ON COLUMN core_scores.end_date IS 'End date of the period the score is valid for. If not filled, score is valid during entire period';
COMMENT ON COLUMN core_scores.score IS 'dimension_id of the location for the dimension';
COMMENT ON COLUMN core_scores.raw_value_formatted IS 'Raw value of the score, formatted for display';
COMMENT ON COLUMN core_scores.updated_at IS 'Timestamp of the last update of the score table';