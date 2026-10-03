DROP VIEW IF EXISTS flagged_days;
DROP VIEW IF EXISTS daily_performance;
DROP VIEW IF EXISTS inverter_summary;

-- One row per inverter per day, with the plant average beside it
CREATE VIEW daily_performance AS
WITH daily AS (
    SELECT DATE(r.reading_time) AS day,
           r.plant_id,
           r.inverter_id,
           SUM(r.ac_power) / 4.0 AS actual_kwh,
           SUM(p.expected_ac) / 4.0 AS expected_kwh,
           SUM(CASE WHEN r.status = 'down' THEN 1 ELSE 0 END) / 4.0 AS hours_down
    FROM readings AS r
    JOIN performance AS p
      ON p.reading_time = r.reading_time AND p.inverter_id = r.inverter_id
    GROUP BY day, r.inverter_id
)
SELECT day,
       plant_id,
       inverter_id,
       ROUND(actual_kwh) AS actual_kwh,
       ROUND(expected_kwh) AS expected_kwh,
       hours_down,
       ROUND(actual_kwh / expected_kwh, 3) AS performance_ratio,
       ROUND(AVG(actual_kwh / expected_kwh) OVER (PARTITION BY day, plant_id), 3)
           AS plant_avg_ratio
FROM daily;

-- Days where an inverter fell well short, with the likely reason
CREATE VIEW flagged_days AS
SELECT day,
       plant_id,
       inverter_id,
       performance_ratio,
       plant_avg_ratio,
       hours_down,
       expected_kwh - actual_kwh AS lost_kwh,
       CASE WHEN hours_down >= 1 THEN 'downtime' ELSE 'underperforming' END AS reason
FROM daily_performance
WHERE performance_ratio < 0.75;

-- One row per inverter for the whole period
CREATE VIEW inverter_summary AS
SELECT r.plant_id,
       r.inverter_id,
       ROUND(SUM(r.ac_power) / 4.0) AS actual_kwh,
       ROUND(SUM(p.expected_ac) / 4.0) AS expected_kwh,
       ROUND(SUM(r.ac_power) / SUM(p.expected_ac), 3) AS performance_ratio,
       ROUND(SUM(p.expected_ac - r.ac_power) / 4.0) AS lost_kwh,
       ROUND(SUM(CASE WHEN r.status = 'down' THEN p.expected_ac ELSE 0 END) / 4.0)
           AS lost_to_downtime_kwh,
       ROUND(100.0 * (1 - SUM(CASE WHEN r.status = 'down' THEN 1.0 ELSE 0 END)
                          / SUM(CASE WHEN r.irradiation > 0.1 THEN 1 ELSE 0 END)), 1)
           AS availability_pct
FROM readings AS r
JOIN performance AS p
  ON p.reading_time = r.reading_time AND p.inverter_id = r.inverter_id
GROUP BY r.inverter_id;