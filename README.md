# TechPoint Data Platform

Operational data-engineering platform for TechPoint. The project ingests the business workbook into an observable DuckDB bronze layer, preserves source lineage, validates quality, and exposes pipeline health through Streamlit.

## First vertical slice

```powershell
py -3.13 -m pip install -r requirements.txt
$env:TECHPOINT_SOURCE_XLSX = 'path\to\techpoint_source.xlsx'
py -3.13 pipelines/ingest.py
py -3.13 pipelines/transform.py
py -3.13 pipelines/quality.py
py -3.13 -m streamlit run app/app.py
```

The pipeline now delivers Excel-to-DuckDB bronze ingestion, a typed Silver table, exception quarantine, required-sheet contract validation, source lineage, SHA-256 source fingerprinting, persistent pipeline run metadata, JSON logs, quality checks, and a Streamlit monitoring dashboard. Negative payments are retained in quarantine until they are classified as refunds or adjustments.

Raw business workbooks are intentionally ignored by Git. The source path is supplied through `TECHPOINT_SOURCE_XLSX` so private business data is not published accidentally.

## Roadmap

Silver cleaning and quarantine, schema-drift detection, incremental loads, gold business marts, orchestration, alerting, and historical quality trends will build on this slice.
