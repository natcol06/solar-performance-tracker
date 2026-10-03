import sqlite3

import pandas as pd
from pvlib.pvsystem import pvwatts_dc

DB_PATH = "solar.db"
TEMP_COEFF = -0.004  # panels lose about 0.4% of power per degree C above 25
STRONG_SUN = 0.6     # kW per square meter


def model_output(df, capacity):
    """Expected power from sunlight, panel temperature, and capacity."""
    return pvwatts_dc(df["irradiation"] * 1000, df["module_temp"], capacity, TEMP_COEFF)


def estimate_capacity(df):
    """Estimate one inverter's capacity for each plant from its best readings."""
    good = df[(df["irradiation"] > STRONG_SUN) & (df["status"] == "ok")]
    implied = good["ac_power"] / model_output(good, 1.0)
    return implied.groupby(good["plant_id"]).quantile(0.90)


def main():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM readings WHERE irradiation > 0", conn)

    capacity = estimate_capacity(df)
    print("Estimated capacity per inverter (kW):")
    print(capacity.round(0).to_string())

    df["expected_ac"] = model_output(df, df["plant_id"].map(capacity))
    df[["reading_time", "inverter_id", "expected_ac"]].to_sql(
        "performance", conn, if_exists="replace", index=False
    )

    by_plant = pd.read_sql(
        """
        SELECT r.plant_id,
               ROUND(SUM(r.ac_power) / 4.0) AS actual_kwh,
               ROUND(SUM(p.expected_ac) / 4.0) AS expected_kwh,
               ROUND(SUM(r.ac_power) / SUM(p.expected_ac), 3) AS performance_ratio
        FROM readings AS r
        JOIN performance AS p
          ON p.reading_time = r.reading_time AND p.inverter_id = r.inverter_id
        GROUP BY r.plant_id
        """,
        conn,
    )
    print("\n===== Performance ratio by plant =====")
    print(by_plant.to_string(index=False))

    worst = pd.read_sql(
        """
        SELECT r.plant_id,
               r.inverter_id,
               ROUND(SUM(r.ac_power) / 4.0) AS actual_kwh,
               ROUND(SUM(p.expected_ac) / 4.0) AS expected_kwh,
               ROUND(SUM(r.ac_power) / SUM(p.expected_ac), 3) AS performance_ratio
        FROM readings AS r
        JOIN performance AS p
          ON p.reading_time = r.reading_time AND p.inverter_id = r.inverter_id
        GROUP BY r.inverter_id
        ORDER BY performance_ratio
        LIMIT 5
        """,
        conn,
    )
    print("\n===== 5 lowest inverters =====")
    print(worst.to_string(index=False))
    conn.close()


if __name__ == "__main__":
    main()