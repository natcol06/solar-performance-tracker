import sqlite3
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
DB_PATH = "solar.db"

# Standardize the dates.
def parse_times(col):
    """Turn date text into one standard format. The files use two styles."""
    year_first = col.iloc[0][:4].isdigit()
    fmt = "%Y-%m-%d %H:%M:%S" if year_first else "%d-%m-%Y %H:%M"
    return pd.to_datetime(col, format=fmt).dt.strftime("%Y-%m-%d %H:%M:%S")

# Reads a plant's CSVs, renames columns to match the schema,
# remove repeated rows, and write them into the database.
def load_plant(conn, number):
    gen = pd.read_csv(RAW / f"Plant_{number}_Generation_Data.csv")
    weather = pd.read_csv(RAW / f"Plant_{number}_Weather_Sensor_Data.csv")
    plant_id = int(gen["PLANT_ID"].iloc[0])

    gen["reading_time"] = parse_times(gen["DATE_TIME"])
    weather["reading_time"] = parse_times(weather["DATE_TIME"])

    conn.execute("INSERT INTO plants (plant_id) VALUES (?)", (plant_id,))

    inverters = pd.DataFrame(
        {"inverter_id": gen["SOURCE_KEY"].unique(), "plant_id": plant_id}
    )
    inverters.to_sql("inverters", conn, if_exists="append", index=False)

    gen_table = gen.rename(
        columns={
            "SOURCE_KEY": "inverter_id",
            "DC_POWER": "dc_power",
            "AC_POWER": "ac_power",
            "DAILY_YIELD": "daily_yield",
            "TOTAL_YIELD": "total_yield",
        }
    )[["reading_time", "inverter_id", "dc_power", "ac_power", "daily_yield", "total_yield"]]
    gen_table = gen_table.drop_duplicates(subset=["reading_time", "inverter_id"])
    gen_table.to_sql("generation", conn, if_exists="append", index=False)

    weather_table = weather.rename(
        columns={
            "PLANT_ID": "plant_id",
            "AMBIENT_TEMPERATURE": "ambient_temp",
            "MODULE_TEMPERATURE": "module_temp",
            "IRRADIATION": "irradiation",
        }
    )[["reading_time", "plant_id", "ambient_temp", "module_temp", "irradiation"]]
    weather_table = weather_table.drop_duplicates(subset=["reading_time", "plant_id"])
    weather_table.to_sql("weather", conn, if_exists="append", index=False)

# Creates the database file, runs the schema, loads both plants, 
# then prints rows counts as a check.
def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(Path("sql/schema.sql").read_text())

    for number in (1, 2):
        load_plant(conn, number)
    conn.commit()

    for table in ("plants", "inverters", "generation", "weather"):
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count} rows")

    sample = pd.read_sql(
        """
        SELECT g.reading_time, g.inverter_id, g.ac_power, w.irradiation
        FROM generation AS g
        JOIN inverters AS i ON g.inverter_id = i.inverter_id
        JOIN weather AS w
          ON w.plant_id = i.plant_id AND w.reading_time = g.reading_time
        WHERE w.irradiation > 0
        LIMIT 5
        """,
        conn,
    )
    print(sample)
    conn.close()


if __name__ == "__main__":
    main()