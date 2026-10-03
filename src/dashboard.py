import sqlite3

import pandas as pd
import streamlit as st

DB_PATH = "solar.db"


@st.cache_data
def query(sql, params=()):
    """Run a SQL query and return the result as a table."""
    conn = sqlite3.connect(DB_PATH)
    result = pd.read_sql(sql, conn, params=params)
    conn.close()
    return result


st.set_page_config(page_title="Solar Performance Tracker", layout="wide")
st.title("Solar Performance Tracker")

plants = query("SELECT plant_id FROM plants")["plant_id"].tolist()
plant = st.sidebar.selectbox("Plant", plants)

summary = query(
    "SELECT * FROM inverter_summary WHERE plant_id = ? ORDER BY performance_ratio",
    (plant,),
)
actual = summary["actual_kwh"].sum()
expected = summary["expected_kwh"].sum()
lost = summary["lost_kwh"].sum()
downtime_loss = summary["lost_to_downtime_kwh"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Performance ratio", f"{actual / expected:.3f}")
col2.metric("Energy lost (kWh)", f"{lost:,.0f}")
col3.metric("Share of loss from downtime", f"{downtime_loss / lost:.0%}")
col4.metric("Average availability", f"{summary['availability_pct'].mean():.1f}%")

st.subheader("Daily energy: actual vs expected")
daily = query(
    """
    SELECT day,
           SUM(actual_kwh) AS actual_kwh,
           SUM(expected_kwh) AS expected_kwh
    FROM daily_performance
    WHERE plant_id = ?
    GROUP BY day
    """,
    (plant,),
)
st.line_chart(daily, x="day", y=["actual_kwh", "expected_kwh"])

st.subheader("Performance ratio by inverter")
st.bar_chart(summary, x="inverter_id", y="performance_ratio")

st.subheader("Flagged days")
flags = query(
    "SELECT * FROM flagged_days WHERE plant_id = ? ORDER BY lost_kwh DESC",
    (plant,),
)
st.dataframe(flags, hide_index=True)

st.subheader("Look closer at one inverter")
inverter = st.selectbox("Inverter (worst first)", summary["inverter_id"])
days = query(
    "SELECT day FROM daily_performance WHERE inverter_id = ? ORDER BY day",
    (inverter,),
)["day"]
day = st.selectbox("Day", days)
detail = query(
    """
    SELECT r.reading_time,
           r.ac_power AS actual_kw,
           p.expected_ac AS expected_kw
    FROM readings AS r
    JOIN performance AS p
      ON p.reading_time = r.reading_time AND p.inverter_id = r.inverter_id
    WHERE r.inverter_id = ? AND DATE(r.reading_time) = ?
    """,
    (inverter, day),
)
st.line_chart(detail, x="reading_time", y=["actual_kw", "expected_kw"])