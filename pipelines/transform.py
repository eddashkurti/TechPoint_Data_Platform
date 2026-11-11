"""Transform bronze sales into typed Silver data and quarantine exceptions."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "techpoint.duckdb"


def run() -> dict:
    con = duckdb.connect(str(DB_PATH))
    con.execute("""
        CREATE OR REPLACE TABLE silver_sales AS
        SELECT
            CAST(source_sheet AS VARCHAR) AS month_sheet,
            CAST(source_row AS INTEGER) AS source_row,
            TRIM(CAST(Emri AS VARCHAR)) AS customer_name,
            NULLIF(TRIM(CAST(Produkti AS VARCHAR)), '') AS product,
            CAST(Pagesa AS DECIMAL(12,2)) AS payment_amount,
            CAST(Posta AS DECIMAL(12,2)) AS shipping_cost,
            CAST(Mall AS DECIMAL(12,2)) AS goods_cost,
            CAST(Net AS DECIMAL(12,2)) AS source_net_amount,
            CASE WHEN Pagesa < 0 THEN 'REFUND_OR_ADJUSTMENT' ELSE 'SALE' END AS transaction_type,
            CAST(ingested_at AS TIMESTAMP) AS ingested_at
        FROM bronze_sales
        WHERE Emri IS NOT NULL AND TRIM(CAST(Emri AS VARCHAR)) <> ''
          AND Pagesa IS NOT NULL
          AND Pagesa >= 0
    """)
    con.execute("""
        CREATE OR REPLACE TABLE quarantine_sales AS
        SELECT *,
               CASE
                 WHEN Pagesa < 0 THEN 'NEGATIVE_PAYMENT_REQUIRES_CLASSIFICATION'
                 WHEN Emri IS NULL OR TRIM(CAST(Emri AS VARCHAR)) = '' THEN 'MISSING_CUSTOMER_NAME'
                 WHEN Pagesa IS NULL THEN 'MISSING_PAYMENT'
                 ELSE 'OTHER_VALIDATION_FAILURE'
               END AS quarantine_reason
        FROM bronze_sales
        WHERE Pagesa < 0 OR Emri IS NULL OR TRIM(CAST(Emri AS VARCHAR)) = '' OR Pagesa IS NULL
    """)
    return {
        "silver_rows": con.execute("SELECT COUNT(*) FROM silver_sales").fetchone()[0],
        "quarantine_rows": con.execute("SELECT COUNT(*) FROM quarantine_sales").fetchone()[0],
    }


if __name__ == "__main__":
    print(run())
