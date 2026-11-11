from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipelines.ingest import normalize_month

def test_normalize_month_preserves_lineage():
    import pandas as pd
    frame = pd.DataFrame([["header", "product", "pay", "post", "goods", "net"], ["Ana", "x", 10, 2, 3, 5]])
    result = normalize_month("Janar 2024", frame)
    assert len(result) == 1
    assert result.iloc[0].source_sheet == "Janar 2024"
    assert result.iloc[0].source_row == 3
