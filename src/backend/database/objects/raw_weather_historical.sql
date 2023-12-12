CREATE TABLE raw_weather_historical (
    location_id                 INT,
    year                        INT,
    month                       INT,
    temperature_max             NUMERIC(10,5),
    temperature_min             NUMERIC(10,5),
    sunshine_duration           NUMERIC(10,5),
    daylight_duration           NUMERIC(10,5),
    precipitation_duration      NUMERIC(10,5),
    precipitation_sum           NUMERIC(10,5),
    rain_sum                    NUMERIC(10,5),
    snowfall_sum                NUMERIC(10,5),
    wind_speed_max              NUMERIC(11,7),
    weather_code_label          VARCHAR(255),
    updated_at                  TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    PRIMARY KEY (location_id, year, month),
    FOREIGN KEY (location_id) REFERENCES core_locations(location_id)
);

COMMENT ON TABLE raw_weather_historical IS 'Table stores current and future weather data for all destinations.';

COMMENT ON COLUMN raw_weather_historical.location_id IS 'Foreign key to the location table';
COMMENT ON COLUMN raw_weather_historical.year IS 'Year for the weather data point';
COMMENT ON COLUMN raw_weather_historical.month IS 'Month for the weather data point';
COMMENT ON COLUMN raw_weather_historical.temperature_max IS 'Recorded maximum temperature';
COMMENT ON COLUMN raw_weather_historical.temperature_min IS 'Recorded minimum temperature';
COMMENT ON COLUMN raw_weather_current_future.sunshine_duration IS 'Duration of sunshine';
COMMENT ON COLUMN raw_weather_current_future.daylight_duration IS 'Duration of daylight';
COMMENT ON COLUMN raw_weather_current_future.precipitation_duration IS 'Duration of percipitation';
COMMENT ON COLUMN raw_weather_historical.precipitation_sum IS 'Total amount of percipitation';
COMMENT ON COLUMN raw_weather_historical.rain_sum IS 'Total amount of rain';
COMMENT ON COLUMN raw_weather_historical.snowfall_sum IS 'Total amount of snowfall';
COMMENT ON COLUMN raw_weather_historical.wind_speed_max IS 'Maximum windspeed';
COMMENT ON COLUMN raw_weather_historical.weather_code_label IS 'Verbal description of the weather code';
COMMENT ON COLUMN raw_weather_historical.updated_at IS 'Timestamp of the last update of the record';