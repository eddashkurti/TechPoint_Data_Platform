# TechPoint Data Platform

An observable data platform for TechPoint’s transactional business data. The project turns a private Excel source into validated, traceable, analytics-ready datasets and a Streamlit workspace for both data operations and business analysis.

## What this demonstrates

TechPoint Data Platform is the data-engineering counterpart to the PulseMetrics analytics project. It focuses on how reliable data is produced, tested, traced, and served—not only on the final chart.

```text
Source workbook
      ↓
Bronze ingestion and lineage
      ↓
Silver typing and quarantine
      ↓
Gold business marts
      ↓
Streamlit operations and analytics
```

## Platform capabilities

- SHA-256 source fingerprinting and incremental skip detection.
- Historical source snapshots and pipeline-run metadata.
- Schema contracts with drift detection.
- Bronze, Silver, and Gold data layers.
- Typed Silver records with row-level quarantine.
- Persistent quality-check history and operational alerts.
- Source sheet and source-row lineage.
- Gold sales, product, customer, reconciliation, and data-health marts.
- Streamlit views for pipeline operations and business analysis.
- GitHub Actions compilation and regression validation.

## Business analytics in the app

The Streamlit workspace includes:

- Monthly sales performance and order volume.
- Product sales and operating-net contribution.
- Top-customer concentration.
- Source-net versus recomputed-net reconciliation.
- Bronze/Silver/quarantine coverage.
- Quality history and pipeline snapshots.

The reconciliation view is intentionally explicit: the source workbook’s recorded `Net` value is compared with the platform’s recomputed value, making source-definition differences visible instead of silently blending them into a KPI.

## Run locally

Keep the private workbook outside Git and provide its path through an environment variable:

```powershell
py -3.13 -m pip install -r requirements.txt
$env:TECHPOINT_SOURCE_XLSX = 'path\to\techpoint_source.xlsx'
py -3.13 pipelines/schema_check.py
py -3.13 pipelines/orchestrate.py
py -3.13 -m streamlit run app/app.py
```

Use `py -3.13 pipelines/orchestrate.py --force` to rebuild intentionally. If the source fingerprint is unchanged, ingestion returns `SKIPPED_UNCHANGED` while downstream marts and quality history remain available.

## Repository structure

```text
app/                 Streamlit operations and analytics app
data/raw/            Local private source files, ignored by Git
metadata/            Data contracts
pipelines/           Ingestion, validation, transformation, marts, orchestration
tests/               Regression tests
docs/                Architecture and design decisions
logs/                Local structured run logs, ignored by Git
```

## Data handling

Raw business files are intentionally excluded from the public repository. The platform stores source fingerprints and lineage metadata, not the private workbook itself. Negative payments are quarantined for business classification as refunds or adjustments.
