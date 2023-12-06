DROP TABLE IF EXISTS log_history;

CREATE TABLE log_history (
    process_id                  VARCHAR(10) NOT NULL,
    start_datetime              TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01') NOT NULL,
    status                      VARCHAR(32),
    end_datetime                TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc-01'),
    exit_code                   INT,
    triggered                   VARCHAR(32),
    last_exec                   DATE,
    next_exec_scheduled         DATE,
    PRIMARY KEY (process_id, start_datetime)
);

COMMENT ON TABLE log_history IS 'Table stores history of all log messages for inserting data into the database.';

COMMENT ON COLUMN log_history.process_id IS 'Unique identifier for table insert function';
COMMENT ON COLUMN log_history.start_datetime IS 'Timepoint when insert process began';
COMMENT ON COLUMN log_history.status IS 'Information whether the insert process is pending, executing or done';
COMMENT ON COLUMN log_history.end_datetime IS 'Timepoint when insert process finished';
COMMENT ON COLUMN log_history.exit_code IS 'Records whether the insert was executed successfully (0) or not (1)';
COMMENT ON COLUMN log_history.triggered IS 'Records whether the insert was triggered manually or automatically';
COMMENT ON COLUMN log_history.last_exec IS 'Last execution of this table insert function';
COMMENT ON COLUMN log_history.next_exec_scheduled IS 'Next timepoint for when an executing of this table insert function is planned';