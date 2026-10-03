DROP VIEW IF EXISTS readings;
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

CREATE VIEW readings AS
SELECT g.reading_time,
       i.plant_id,
       g.inverter_id,
       g.dc_power,
       g.ac_power,
       g.daily_yield,
       w.ambient_temp,
       w.module_temp,
       w.irradiation,
       CASE
           WHEN w.irradiation > 0.1 AND g.ac_power = 0 THEN 'down'
           WHEN w.irradiation = 0 AND g.ac_power > 0 THEN 'suspect'
           ELSE 'ok'
       END AS status
FROM generation AS g
JOIN inverters AS i ON g.inverter_id = i.inverter_id
JOIN weather AS w
  ON w.plant_id = i.plant_id AND w.reading_time = g.reading_time;