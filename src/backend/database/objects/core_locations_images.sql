CREATE TABLE core_locations_images (
    location_id         INTEGER PRIMARY KEY NOT NULL,
    img_url             VARCHAR(1024),
    source              TEXT,
    updated_at          TIMESTAMP
);

COMMENT ON TABLE core_locations_images IS 'Table stores image links and their sources for all locations.';

COMMENT ON COLUMN core_locations_images.location_id IS 'Unique identifier for the location';
COMMENT ON COLUMN core_locations_images.img_url IS 'URL linking to the image';
COMMENT ON COLUMN core_locations_images.source IS 'Source attributed to the image';
COMMENT ON COLUMN core_locations_images.updated_at IS 'Timestamp of the last update of the record';