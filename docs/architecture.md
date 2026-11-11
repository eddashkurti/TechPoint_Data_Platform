# TechPoint Data Platform architecture

## Current flow

```text
TechPoint source workbook
        ↓
Contract validation
        ↓
Bronze DuckDB table: bronze_sales
        ↓
Quality checks + lineage metadata
        ↓
Streamlit observability app
```

The bronze layer preserves the original business fields while adding `source_sheet`, `source_row`, `ingested_at`, and pipeline-run metadata. This makes every row traceable back to its workbook location.

## Design decisions

- Raw workbooks stay outside Git because they contain private business data.
- The source file is fingerprinted with SHA-256 for reproducibility.
- Pipeline runs are append-only so repeated loads remain observable.
- Negative payments are warnings until the business confirms whether they represent refunds or corrections.
- DuckDB is used as the local analytical engine because it is portable and requires no server.

## Next layers

The next implementation phase will add a Silver table with standardized names, typed dates, explicit refund classification, and a quarantine table for records that cannot be safely modeled.
