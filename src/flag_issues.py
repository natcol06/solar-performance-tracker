import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = "solar.db"

REPORTS = {
    "Where the lost energy went, by plant": """
        SELECT plant_id,
               SUM(lost_kwh) AS lost_kwh,
               SUM(lost_to_downtime_kwh) AS lost_to_downtime_kwh,
               ROUND(100.0 * SUM(lost_to_downtime_kwh) / SUM(lost_kwh), 1)
                   AS pct_from_downtime
        FROM inverter_summary
        GROUP BY plant_id
    """,
    "10 worst inverters": """
        SELECT * FROM inverter_summary
        ORDER BY performance_ratio
        LIMIT 10
    """,
    "Flagged days by reason": """
        SELECT plant_id,
               reason,
               COUNT(*) AS flagged_days,
               SUM(lost_kwh) AS lost_kwh
        FROM flagged_days
        GROUP BY plant_id, reason
    """,
    "10 worst single days": """
        SELECT * FROM flagged_days
        ORDER BY lost_kwh DESC
        LIMIT 10
    """,
}


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(Path("sql/analysis.sql").read_text())
    for title, query in REPORTS.items():
        print(f"\n===== {title} =====")
        result = pd.read_sql(query, conn)
        print("No rows found." if result.empty else result.to_string(index=False))
    conn.close()


if __name__ == "__main__":
    main()