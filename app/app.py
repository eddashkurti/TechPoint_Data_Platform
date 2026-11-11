"""TechPoint data-platform observability dashboard."""
from pathlib import Path
import duckdb
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "techpoint.duckdb"
st.set_page_config(page_title="TechPoint Data Platform", page_icon="◈", layout="wide")
st.title("TechPoint Data Platform")
st.caption("Pipeline observability · data quality · lineage · operational readiness")
if not DB_PATH.exists():
    st.warning("No local pipeline database exists yet. Run `py pipelines/ingest.py` first.")
    st.stop()
con = duckdb.connect(str(DB_PATH), read_only=True)
latest = con.execute("SELECT * FROM pipeline_runs ORDER BY finished_at DESC LIMIT 1").df()
row_count = int(con.execute("SELECT COUNT(*) FROM bronze_sales").fetchone()[0])
sheet_count = int(con.execute("SELECT COUNT(DISTINCT source_sheet) FROM bronze_sales").fetchone()[0])
source_count = int(con.execute("SELECT COUNT(DISTINCT source_file) FROM pipeline_runs").fetchone()[0])
cols = st.columns(4)
cols[0].metric("Latest run", latest.iloc[0].status if not latest.empty else "Unknown")
cols[1].metric("Bronze rows", f"{row_count:,}")
cols[2].metric("Source sheets", f"{sheet_count:,}")
cols[3].metric("Source files", f"{source_count:,}")
left, right = st.columns(2)
with left:
    st.subheader("Rows by source sheet")
    by_sheet = con.execute("SELECT source_sheet, COUNT(*) AS rows FROM bronze_sales GROUP BY 1 ORDER BY 1").df()
    st.plotly_chart(px.bar(by_sheet, x="source_sheet", y="rows", title="Bronze ingestion volume"), width="stretch")
with right:
    st.subheader("Pipeline checks")
    checks = con.execute("SELECT 'Rows loaded' AS check, COUNT(*) AS value, CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END AS status FROM bronze_sales UNION ALL SELECT 'Negative payments', COUNT(*), CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END FROM bronze_sales WHERE Pagesa < 0 UNION ALL SELECT 'Missing lineage', COUNT(*), CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END FROM bronze_sales WHERE source_sheet IS NULL OR source_row IS NULL").df()
    st.dataframe(checks, hide_index=True, width="stretch")
st.subheader("Recent pipeline runs")
st.dataframe(con.execute("SELECT run_id, source_file, source_sha256, started_at, finished_at, status, row_count, sheet_count FROM pipeline_runs ORDER BY finished_at DESC").df(), hide_index=True, width="stretch")
