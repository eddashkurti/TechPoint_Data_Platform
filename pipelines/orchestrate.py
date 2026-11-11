"""Run the TechPoint pipeline in dependency order."""
from ingest import run as ingest
from transform import run as transform
from gold import run as gold
from quality import run as quality


if __name__ == "__main__":
    results = {"ingest": ingest(), "transform": transform(), "gold": gold(), "quality": quality()}
    if any(item["status"] == "FAIL" for item in results["quality"]):
        raise SystemExit(1)
    print(results)
