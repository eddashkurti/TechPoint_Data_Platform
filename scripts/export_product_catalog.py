"""Export the complete raw product-label catalog for business mapping review."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "product_catalog.csv"
con = duckdb.connect(str(ROOT / "techpoint.duckdb"), read_only=True)
OUT.parent.mkdir(exist_ok=True)
con.execute(f"""
COPY (
    SELECT COALESCE(NULLIF(TRIM(CAST(Produkti AS VARCHAR)), ''), '[blank]') AS raw_product,
           COUNT(*) AS orders,
           ROUND(SUM(CAST(Pagesa AS DOUBLE)), 2) AS sales_eur
    FROM bronze_sales
    GROUP BY 1
    ORDER BY lower(raw_product)
) TO '{OUT.as_posix()}' WITH (HEADER, DELIMITER ',')
""")
print(f"Wrote {OUT}")
