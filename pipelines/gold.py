"""Build Gold business marts from the Silver layer."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "techpoint.duckdb"


def run() -> dict:
    con = duckdb.connect(str(DB_PATH))
    con.execute("""
        CREATE OR REPLACE TABLE gold_monthly_performance AS
        SELECT month_sheet, COUNT(*) AS orders,
               SUM(payment_amount) AS sales,
               SUM(shipping_cost) AS shipping_cost,
               SUM(goods_cost) AS goods_cost,
               SUM(payment_amount - shipping_cost - goods_cost) AS operating_net,
               AVG(payment_amount) AS average_order_value
        FROM silver_sales
        GROUP BY month_sheet ORDER BY month_sheet
    """)
    con.execute("""
        CREATE OR REPLACE TABLE gold_product_performance AS
        SELECT COALESCE(product, 'Unknown') AS product,
               COUNT(*) AS orders, SUM(payment_amount) AS sales,
               SUM(payment_amount - shipping_cost - goods_cost) AS operating_net
        FROM silver_sales GROUP BY 1 ORDER BY sales DESC
    """)
    con.execute("""
        CREATE OR REPLACE TABLE gold_data_health AS
        SELECT CURRENT_TIMESTAMP AS measured_at,
               (SELECT COUNT(*) FROM bronze_sales) AS bronze_rows,
               (SELECT COUNT(*) FROM silver_sales) AS silver_rows,
               (SELECT COUNT(*) FROM quarantine_sales) AS quarantine_rows,
               (SELECT COUNT(*) FROM silver_sales WHERE payment_amount < 0) AS invalid_silver_payments
    """)
    return {"monthly_rows": con.execute("SELECT COUNT(*) FROM gold_monthly_performance").fetchone()[0], "product_rows": con.execute("SELECT COUNT(*) FROM gold_product_performance").fetchone()[0]}


if __name__ == "__main__":
    print(run())
