"""Build Gold business marts from the Silver layer."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "techpoint.duckdb"


def run() -> dict:
    con = duckdb.connect(str(DB_PATH))
    con.execute("""
        CREATE OR REPLACE TABLE gold_monthly_performance AS
        SELECT month_sheet,
               CASE month_sheet
                 WHEN 'Janar 2024' THEN 'Janar' WHEN 'Shkurt  2024' THEN 'Shkurt'
                 WHEN 'Mars 2024' THEN 'Mars' WHEN 'Prill 2024' THEN 'Prill'
                 WHEN 'Maj 2024' THEN 'Maj' WHEN 'Qershor 2024' THEN 'Qershor'
                 WHEN 'Korrik 2024' THEN 'Korrik' WHEN 'Gusht 2024' THEN 'Gusht'
                 WHEN 'Shtator 2024' THEN 'Shtator' WHEN 'Tetor 2024' THEN 'Tetor'
                 WHEN 'Nentor 2024' THEN 'Nentor' WHEN 'Dhjetor 2024' THEN 'Dhjetor'
               END AS month_name,
               CASE month_sheet
                 WHEN 'Janar 2024' THEN 1 WHEN 'Shkurt  2024' THEN 2 WHEN 'Mars 2024' THEN 3
                 WHEN 'Prill 2024' THEN 4 WHEN 'Maj 2024' THEN 5 WHEN 'Qershor 2024' THEN 6
                 WHEN 'Korrik 2024' THEN 7 WHEN 'Gusht 2024' THEN 8 WHEN 'Shtator 2024' THEN 9
                 WHEN 'Tetor 2024' THEN 10 WHEN 'Nentor 2024' THEN 11 WHEN 'Dhjetor 2024' THEN 12
               END AS month_order,
               COUNT(*) AS orders,
               SUM(payment_amount) AS sales,
               SUM(shipping_cost) AS shipping_cost,
               SUM(goods_cost) AS goods_cost,
               SUM(payment_amount - shipping_cost - goods_cost) AS operating_net,
               100.0 * SUM(payment_amount - shipping_cost - goods_cost) / NULLIF(SUM(payment_amount), 0) AS margin_pct,
               AVG(payment_amount) AS average_order_value
        FROM silver_sales
        GROUP BY month_sheet ORDER BY month_order
    """)
    con.execute("""
        CREATE OR REPLACE TABLE gold_product_performance AS
        SELECT COALESCE(product, 'Unknown') AS product,
               COUNT(*) AS orders, SUM(payment_amount) AS sales,
               SUM(payment_amount - shipping_cost - goods_cost) AS operating_net,
               100.0 * SUM(payment_amount - shipping_cost - goods_cost) / NULLIF(SUM(payment_amount), 0) AS margin_pct
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
    con.execute("""
        CREATE OR REPLACE TABLE gold_reconciliation AS
        SELECT month_sheet, SUM(source_net_amount) AS source_net,
               SUM(payment_amount - shipping_cost - goods_cost) AS recomputed_net,
               SUM(source_net_amount) - SUM(payment_amount - shipping_cost - goods_cost) AS variance
        FROM silver_sales GROUP BY 1 ORDER BY 1
    """)
    return {"monthly_rows": con.execute("SELECT COUNT(*) FROM gold_monthly_performance").fetchone()[0], "product_rows": con.execute("SELECT COUNT(*) FROM gold_product_performance").fetchone()[0]}


if __name__ == "__main__":
    print(run())
