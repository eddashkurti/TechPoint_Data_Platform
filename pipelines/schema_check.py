"""Validate source workbook sheets against the TechPoint data contract."""
from pathlib import Path
import json
import os
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "raw" / "techpoint_source.xlsx"
MONTH_SHEETS = ["Janar 2024", "Shkurt  2024", "Mars 2024", "Prill 2024", "Maj 2024", "Qershor 2024", "Korrik 2024", "Gusht 2024", "Shtator 2024", "Tetor 2024", "Nentor 2024", "Dhjetor 2024"]
EXPECTED = ["Emri", "Produkti", "Pagesa", "Posta", "Mall", "Net"]


def run(path: Path | None = None) -> dict:
    path = path or Path(os.getenv("TECHPOINT_SOURCE_XLSX", DEFAULT_SOURCE))
    workbook = pd.ExcelFile(path)
    missing_sheets = [sheet for sheet in MONTH_SHEETS if sheet not in workbook.sheet_names]
    unexpected_sheets = [sheet for sheet in workbook.sheet_names if sheet not in MONTH_SHEETS and sheet != "2024"]
    sheet_results = []
    for sheet in MONTH_SHEETS:
        if sheet in missing_sheets:
            continue
        columns = list(pd.read_excel(path, sheet_name=sheet, nrows=0).columns[:6])
        sheet_results.append({"sheet": sheet, "columns": columns, "status": "PASS" if columns == EXPECTED else "DRIFT"})
    result = {"source": str(path), "missing_sheets": missing_sheets, "unexpected_sheets": unexpected_sheets, "sheet_results": sheet_results, "status": "PASS" if not missing_sheets and all(item["status"] == "PASS" for item in sheet_results) else "DRIFT"}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if run()["status"] == "PASS" else 1)
