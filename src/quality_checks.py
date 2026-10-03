import sqlite3

import pandas as pd

DB_PATH = "solar.db"

CHECKS = {
    "1. Missing readings (5 worst inverters)": """
        WITH span AS (
            SELECT (JULIANDAY(MAX(reading_time)) - JULIANDAY(MIN(reading_time))) * 96 + 1
                   AS expected
            FROM generation
        )
        SELECT i.plant_id,
               g.inverter_id,
               COUNT(*) AS actual,
               CAST(ROUND(span.expected) AS INTEGER) AS expected,
               ROUND(100.0 * COUNT(*) / span.expected, 1) AS pct_complete
        FROM generation AS g
        JOIN inverters AS i ON g.inverter_id = i.inverter_id
        CROSS JOIN span
        GROUP BY g.inverter_id
        ORDER BY pct_complete
        LIMIT 5
    """,
    "2. AC to DC ratio by plant (should be a bit under 1)": """
        SELECT i.plant_id,
               ROUND(AVG(g.ac_power / g.dc_power), 3) AS avg_ac_dc_ratio
        FROM generation AS g
        JOIN inverters AS i ON g.inverter_id = i.inverter_id
        WHERE g.dc_power > 0
        GROUP BY i.plant_id
    """,
    "3. Sun is up but inverter makes nothing (5 worst inverters)": """
        SELECT i.plant_id,
               g.inverter_id,
               COUNT(*) AS zero_readings,
               ROUND(COUNT(*) / 4.0, 1) AS hours_down
        FROM generation AS g
        JOIN inverters AS i ON g.inverter_id = i.inverter_id
        JOIN weather AS w
          ON w.plant_id = i.plant_id AND w.reading_time = g.reading_time
        WHERE w.irradiation > 0.1 AND g.ac_power = 0
        GROUP BY g.inverter_id
        ORDER BY zero_readings DESC
        LIMIT 5
    """,
    "4. Power at night (should be 0 rows)": """
        SELECT i.plant_id, COUNT(*) AS night_power_readings
        FROM generation AS g
        JOIN inverters AS i ON g.inverter_id = i.inverter_id
        JOIN weather AS w
          ON w.plant_id = i.plant_id AND w.reading_time = g.reading_time
        WHERE w.irradiation = 0 AND g.ac_power > 0
        GROUP BY i.plant_id
    """,
    "5. Power readings with no weather reading": """
        SELECT i.plant_id, COUNT(*) AS readings_without_weather
        FROM generation AS g
        JOIN inverters AS i ON g.inverter_id = i.inverter_id
        LEFT JOIN weather AS w
          ON w.plant_id = i.plant_id AND w.reading_time = g.reading_time
        WHERE w.reading_time IS NULL
        GROUP BY i.plant_id
    """,
    "6. Reading status counts": """
        SELECT plant_id, status, COUNT(*) AS readings
        FROM readings
        GROUP BY plant_id, status
    """,
}


def main():
    conn = sqlite3.connect(DB_PATH)
    for title, query in CHECKS.items():
        print(f"\n===== {title} =====")
        result = pd.read_sql(query, conn)
        print("No rows found." if result.empty else result.to_string(index=False))
    conn.close()


if __name__ == "__main__":
    main()