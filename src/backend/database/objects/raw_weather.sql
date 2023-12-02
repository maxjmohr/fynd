DROP TABLE IF EXISTS raw_weather;

CREATE TABLE raw_weather (
    weather_id                  VARCHAR(255) PRIMARY KEY NOT NULL,
    date                        DATE,
    weather_code                INT,
    temperature_2m_max          NUMERIC(10,5),
    temperature_2m_min          NUMERIC(10,5),
    apparent_temperature_max    NUMERIC(10,7),
    apparent_temperature_min    NUMERIC(10,7),
    sunrise                     INT,
    sunset                      INT,
    precipitation_sum           NUMERIC(10,5),
    rain_sum                    NUMERIC(10,5),
    snowfall_sum                NUMERIC(10,5),
    wind_speed_10m_max          NUMERIC(11,7),
    weather_code_label          VARCHAR(255),
    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01')
);

COMMENT ON TABLE raw_weather IS 'Table stores weather data for all destinations.';

COMMENT ON COLUMN raw_weather.weather_id IS 'Unique identifier for weather data point';
COMMENT ON COLUMN raw_weather.date IS 'Date for the weather data point';
COMMENT ON COLUMN raw_weather.weather_code IS 'Numerical code for weather type for the weather data point';
COMMENT ON COLUMN raw_weather.temperature_2m_max IS 'Recorded maximum temperature';
COMMENT ON COLUMN raw_weather.temperature_2m_min IS 'Recorded minimum temperature';
COMMENT ON COLUMN raw_weather.apparent_temperature_max IS 'Recorded apparent maximum temperature';
COMMENT ON COLUMN raw_weather.apparent_temperature_min IS 'Recorded apparent minimum temperature';
COMMENT ON COLUMN raw_weather.sunrise IS 'Time of sunrise';
COMMENT ON COLUMN raw_weather.sunset IS 'Time of sunset';
COMMENT ON COLUMN raw_weather.precipitation_sum IS 'Total amount of percipitation';
COMMENT ON COLUMN raw_weather.rain_sum IS 'Total amount of rain';
COMMENT ON COLUMN raw_weather.snowfall_sum IS 'Total amount of snowfall';
COMMENT ON COLUMN raw_weather.wind_speed_10m_max IS 'Maximum windspeed';
COMMENT ON COLUMN raw_weather.weather_code_label IS 'Verbal description of the weather code';
COMMENT ON COLUMN raw_weather.updated_at IS 'Timestamp of the last update of the record';