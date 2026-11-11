# TechPoint Data Platform

Operational data-engineering platform for TechPoint. The project ingests the business workbook into an observable DuckDB bronze layer, preserves source lineage, validates quality, and exposes pipeline health through Streamlit.

## First vertical slice

```powershell
py -3.13 -m pip install -r requirements.txt
$env:TECHPOINT_SOURCE_XLSX = 'path\to\techpoint_source.xlsx'
py -3.13 pipelines/ingest.py
py -3.13 pipelines/orchestrate.py
py -3.13 -m streamlit run app/app.py
```

The pipeline now delivers Bronze ingestion, typed Silver transformation, exception quarantine, Gold monthly/product marts, schema checks, persistent run metadata, historical quality results, JSON logs, and a Streamlit monitoring dashboard. Negative payments are retained in quarantine until they are classified as refunds or adjustments.

Repeated runs fingerprint the source workbook. If the SHA-256 hash is unchanged, ingestion returns `SKIPPED_UNCHANGED`; use `py -3.13 pipelines/orchestrate.py --force` for an intentional rebuild. Every initial or changed source is recorded in `source_snapshots`.

Raw business workbooks are intentionally ignored by Git. The source path is supplied through `TECHPOINT_SOURCE_XLSX` so private business data is not published accidentally.

## Roadmap

Silver cleaning and quarantine, schema-drift detection, incremental loads, gold business marts, orchestration, alerting, and historical quality trends will build on this slice.
