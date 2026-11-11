"""Validate bronze data and report operational checks."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "techpoint.duckdb"
CHECKS = {
    "bronze table exists": "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='bronze_sales'",
    "rows loaded": "SELECT COUNT(*) FROM bronze_sales",
    "missing customer names": "SELECT COUNT(*) FROM bronze_sales WHERE Emri IS NULL OR trim(Emri)=''",
    "negative payments": "SELECT COUNT(*) FROM bronze_sales WHERE Pagesa < 0",
    "missing source lineage": "SELECT COUNT(*) FROM bronze_sales WHERE source_sheet IS NULL OR source_row IS NULL",
}
WARNINGS = {"negative payments"}

def run() -> list[dict]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    results = []
    for name, sql in CHECKS.items():
        value = con.execute(sql).fetchone()[0]
        passed = value > 0 if name in {"bronze table exists", "rows loaded"} else value == 0
        status = "PASS" if passed else ("WARN" if name in WARNINGS else "FAIL")
        results.append({"check": name, "value": value, "status": status})
    return results

if __name__ == "__main__":
    results = run()
    for result in results:
        print(f"{result['status']} | {result['check']}: {result['value']}")
    if any(result["status"] == "FAIL" for result in results):
        raise SystemExit(1)
