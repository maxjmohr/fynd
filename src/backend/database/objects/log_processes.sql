DROP TABLE IF EXISTS log_processes;

CREATE TABLE log_processes (
    process_id                  VARCHAR(10) PRIMARY KEY NOT NULL,
    description                 VARCHAR(255),
    script_params               VARCHAR(255),
    turnus                      VARCHAR(64),
    last_exec                   DATE,
    next_exec_scheduled         DATE
);

COMMENT ON TABLE log_processes IS 'Table stores information on log processes for data insertion functions into the database.';

COMMENT ON COLUMN log_processes.process_id IS 'Unique identifier for table insert function';
COMMENT ON COLUMN log_processes.description IS 'Description of the data insertion function associated with this process_id';
COMMENT ON COLUMN log_processes.script_params IS 'Parameters (e.g. function name) passed to the Python file for execution';
COMMENT ON COLUMN log_processes.turnus IS 'Time interval lies between scheduled updates for this data table';
COMMENT ON COLUMN log_processes.last_exec IS 'Last execution of this table insert function';
COMMENT ON COLUMN log_processes.next_exec_scheduled IS 'Next timepoint for when an executing of this table insert function is planned';