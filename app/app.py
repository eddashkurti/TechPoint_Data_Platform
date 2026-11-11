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
silver_count = int(con.execute("SELECT COUNT(*) FROM silver_sales").fetchone()[0]) if con.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='silver_sales'").fetchone()[0] else 0
quarantine_count = int(con.execute("SELECT COUNT(*) FROM quarantine_sales").fetchone()[0]) if con.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='quarantine_sales'").fetchone()[0] else 0
gold_ready = con.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='gold_monthly_performance'").fetchone()[0] > 0
sheet_count = int(con.execute("SELECT COUNT(DISTINCT source_sheet) FROM bronze_sales").fetchone()[0])
source_count = int(con.execute("SELECT COUNT(DISTINCT source_file) FROM pipeline_runs").fetchone()[0])
snapshot_count = int(con.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='source_snapshots'").fetchone()[0])
cols = st.columns(7)
cols[0].metric("Latest run", latest.iloc[0].status if not latest.empty else "Unknown")
cols[1].metric("Bronze rows", f"{row_count:,}")
cols[2].metric("Silver rows", f"{silver_count:,}")
cols[3].metric("Quarantined", f"{quarantine_count:,}")
cols[4].metric("Source sheets", f"{sheet_count:,}")
cols[5].metric("Source files", f"{source_count:,}")
cols[6].metric("Snapshots", f"{snapshot_count:,}")
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

if quarantine_count:
    st.subheader("Quarantine review")
    st.caption("These records are excluded from Silver until their business meaning is confirmed.")
    st.dataframe(con.execute("SELECT source_sheet, source_row, Emri AS customer_name, Pagesa AS payment_amount, quarantine_reason FROM quarantine_sales ORDER BY source_sheet, source_row").df(), hide_index=True, width="stretch")

if gold_ready:
    st.subheader("Gold business marts")
    gold_left, gold_right = st.columns(2)
    with gold_left:
        monthly = con.execute("SELECT * FROM gold_monthly_performance").df()
        st.plotly_chart(px.line(monthly, x="month_sheet", y="sales", markers=True, title="Sales by source month"), width="stretch")
        st.dataframe(monthly, hide_index=True, width="stretch")
    with gold_right:
        products = con.execute("SELECT * FROM gold_product_performance LIMIT 15").df()
        st.plotly_chart(px.bar(products, x="product", y="sales", title="Top products by sales"), width="stretch")
        st.dataframe(products, hide_index=True, width="stretch")

st.subheader("Quality history and alerts")
history = con.execute("SELECT * FROM quality_history ORDER BY measured_at DESC LIMIT 100").df() if con.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='quality_history'").fetchone()[0] else None
if history is not None and not history.empty:
    failures = history[history.status == "FAIL"]
    if failures.empty:
        st.success("No failing quality checks in the recorded history.")
    else:
        st.error(f"{len(failures)} failing quality check results require attention.")
    st.dataframe(history, hide_index=True, width="stretch")

if snapshot_count:
    st.subheader("Source snapshot history")
    st.dataframe(con.execute("SELECT snapshot_id, source_file, source_sha256, captured_at, row_count, sheet_count, status FROM source_snapshots ORDER BY captured_at DESC").df(), hide_index=True, width="stretch")
