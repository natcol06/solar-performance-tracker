DROP TABLE IF EXISTS generation;
DROP TABLE IF EXISTS weather;
DROP TABLE IF EXISTS inverters;
DROP TABLE IF EXISTS plants;

CREATE TABLE plants (
    plant_id INTEGER PRIMARY KEY
);

CREATE TABLE inverters (
    inverter_id TEXT PRIMARY KEY,
    plant_id    INTEGER NOT NULL REFERENCES plants(plant_id)
);

CREATE TABLE generation (
    reading_time TEXT NOT NULL,
    inverter_id  TEXT NOT NULL REFERENCES inverters(inverter_id),
    dc_power     REAL,
    ac_power     REAL,
    daily_yield  REAL,
    total_yield  REAL,
    PRIMARY KEY (reading_time, inverter_id)
);

CREATE TABLE weather (
    reading_time TEXT NOT NULL,
    plant_id     INTEGER NOT NULL REFERENCES plants(plant_id),
    ambient_temp REAL,
    module_temp  REAL,
    irradiation  REAL,
    PRIMARY KEY (reading_time, plant_id)
);