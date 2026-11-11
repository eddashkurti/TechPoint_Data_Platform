"""TechPoint data-platform observability dashboard."""
from pathlib import Path
import duckdb
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "techpoint.duckdb"
st.set_page_config(page_title="TechPoint Data Platform", page_icon="◈", layout="wide")
st.title("TechPoint Profitability Dashboard")
st.caption("Product sales, operating profit, margin, and data reliability")
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
if gold_ready:
    totals = con.execute("SELECT SUM(sales), SUM(operating_net), SUM(orders), 100.0 * SUM(operating_net) / NULLIF(SUM(sales), 0) FROM gold_monthly_performance").fetchone()
    cols = st.columns(4)
    cols[0].metric("Total sales", f"€{totals[0]:,.0f}")
    cols[1].metric("Operating profit", f"€{totals[1]:,.0f}")
    cols[2].metric("Orders", f"{int(totals[2]):,}")
    cols[3].metric("Operating margin", f"{totals[3]:.1f}%")
if gold_ready:
    st.subheader("Product profitability")
    st.caption("Products are ranked by operating profit after shipping and goods costs.")
    gold_left, gold_right = st.columns(2)
    with gold_left:
        monthly = con.execute("SELECT * FROM gold_monthly_performance").df()
        fig = px.line(monthly.sort_values("month_order"), x="month_name", y=["sales", "operating_net"], markers=True, title="Sales and operating profit by month")
        st.plotly_chart(fig, width="stretch")
    with gold_right:
        products = con.execute("SELECT * FROM gold_product_performance ORDER BY operating_net DESC LIMIT 15").df()
        st.plotly_chart(px.bar(products.head(10), x="product", y="operating_net", title="Top products by operating profit"), width="stretch")
    products = con.execute("SELECT * FROM gold_product_performance ORDER BY operating_net DESC").df()
    st.dataframe(products, hide_index=True, width="stretch", column_config={"sales": st.column_config.NumberColumn(format="€%d"), "operating_net": st.column_config.NumberColumn(format="€%d"), "margin_pct": st.column_config.NumberColumn(format="%.1f%%")})
    st.subheader("Monthly operating costs and orders")
    monthly_costs = monthly.sort_values("month_order")
    cost_left, cost_right = st.columns(2)
    with cost_left:
        st.plotly_chart(px.bar(monthly_costs, x="month_name", y="orders", title="Orders per month"), width="stretch")
    with cost_right:
        st.plotly_chart(px.bar(monthly_costs, x="month_name", y=["shipping_cost", "goods_cost"], title="Posta and Mall cost per month"), width="stretch")
    with st.expander("Profit reconciliation"):
        reconciliation = con.execute("SELECT * FROM gold_reconciliation").df()
        st.dataframe(reconciliation, hide_index=True, width="stretch")

with st.expander("Data reliability and pipeline status"):
    st.caption("Operational details are kept available for trust and troubleshooting without competing with the profitability analysis. Currency is EUR. Posta is shipping/post-office cost; Mall is supplier product cost.")
    ops = st.columns(5)
    ops[0].metric("Latest run", latest.iloc[0].status if not latest.empty else "Unknown")
    ops[1].metric("Validated rows", f"{silver_count:,}")
    ops[2].metric("Quarantined", f"{quarantine_count:,}")
    ops[3].metric("Source sheets", f"{sheet_count:,}")
    ops[4].metric("Snapshots", f"{snapshot_count:,}")
    if quarantine_count:
        st.warning(f"{quarantine_count} records are excluded from profitability metrics pending classification.")

st.subheader("Quality status")
history = con.execute("SELECT * FROM quality_history ORDER BY measured_at DESC LIMIT 100").df() if con.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='quality_history'").fetchone()[0] else None
if history is not None and not history.empty:
    failures = history[history.status == "FAIL"]
    if failures.empty:
        st.success("No failing quality checks in the recorded history.")
    else:
        st.error(f"{len(failures)} failing quality check results require attention.")
    st.dataframe(history[["check_name", "value", "status", "measured_at"]], hide_index=True, width="stretch")
