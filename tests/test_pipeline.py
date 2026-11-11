from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipelines.ingest import normalize_month
from pipelines.transform import run as transform_run
from pipelines.gold import run as gold_run
from pipelines.ingest import run as ingest_run

def test_normalize_month_preserves_lineage():
    import pandas as pd
    frame = pd.DataFrame([["header", "product", "pay", "post", "goods", "net"], ["Ana", "x", 10, 2, 3, 5]])
    result = normalize_month("Janar 2024", frame)
    assert len(result) == 1
    assert result.iloc[0].source_sheet == "Janar 2024"
    assert result.iloc[0].source_row == 3


def test_transform_separates_quarantine_records():
    result = transform_run()
    assert result["silver_rows"] > 0
    assert result["quarantine_rows"] == 9


def test_gold_marts_build():
    result = gold_run()
    assert result["monthly_rows"] == 12
    assert result["product_rows"] > 0
    assert result["customer_rows"] > 0


def test_unchanged_source_is_skipped():
    result = ingest_run()
    assert result["status"] == "SKIPPED_UNCHANGED"
