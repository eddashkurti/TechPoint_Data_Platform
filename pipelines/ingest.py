"""Ingest TechPoint's monthly Excel workbook into a DuckDB bronze layer."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "raw" / "techpoint_source.xlsx"
DB_PATH = ROOT / "techpoint.duckdb"
MONTH_SHEETS = [
    "Janar 2024", "Shkurt  2024", "Mars 2024", "Prill 2024", "Maj 2024",
    "Qershor 2024", "Korrik 2024", "Gusht 2024", "Shtator 2024", "Tetor 2024",
    "Nentor 2024", "Dhjetor 2024",
]


def source_path() -> Path:
    value = os.getenv("TECHPOINT_SOURCE_XLSX")
    return Path(value) if value else DEFAULT_SOURCE


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_month(sheet: str, frame: pd.DataFrame) -> pd.DataFrame:
    expected = ["Emri", "Produkti", "Pagesa", "Posta", "Mall", "Net"]
    frame = frame.iloc[:, :6].copy()
    frame.columns = expected
    frame = frame.iloc[1:].copy()
    frame["source_sheet"] = sheet
    frame["source_row"] = range(3, len(frame) + 3)
    frame["ingested_at"] = datetime.now(timezone.utc).isoformat()
    for col in ["Pagesa", "Posta", "Mall", "Net"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame[frame["Emri"].notna() & frame["Pagesa"].notna()]


def run(path: Path = None) -> dict:
    path = path or source_path()
    if not path.exists():
        raise FileNotFoundError(f"TechPoint source workbook not found: {path}")
    started = datetime.now(timezone.utc)
    workbook = pd.ExcelFile(path)
    missing = [sheet for sheet in MONTH_SHEETS if sheet not in workbook.sheet_names]
    if missing:
        raise ValueError(f"Missing required monthly sheets: {missing}")
    monthly = pd.concat([normalize_month(sheet, pd.read_excel(path, sheet_name=sheet, header=0)) for sheet in MONTH_SHEETS], ignore_index=True)
    con = duckdb.connect(str(DB_PATH))
    con.register("monthly_frame", monthly)
    con.execute("CREATE OR REPLACE TABLE bronze_sales AS SELECT * FROM monthly_frame")
    con.execute("CREATE TABLE IF NOT EXISTS pipeline_runs (run_id VARCHAR, source_file VARCHAR, source_sha256 VARCHAR, started_at TIMESTAMP, finished_at TIMESTAMP, status VARCHAR, row_count BIGINT, sheet_count INTEGER, error_message VARCHAR)")
    run_id = started.strftime("%Y%m%dT%H%M%SZ")
    finished = datetime.now(timezone.utc)
    con.execute("INSERT INTO pipeline_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [run_id, str(path), fingerprint(path), started, finished, "SUCCESS", len(monthly), len(MONTH_SHEETS), None])
    summary = {"run_id": run_id, "source": str(path), "rows": len(monthly), "sheets": len(MONTH_SHEETS), "status": "SUCCESS"}
    (ROOT / "logs").mkdir(exist_ok=True)
    (ROOT / "logs" / f"{run_id}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
