# Data Project Template

A lightweight Python starting point for data projects. It provides a practical data lifecycle and optional profiling and data-contract capabilities while leaving storage, compute, deployment, and integration choices to each project.

## Setup

This template requires Python 3.12 or later and [uv](https://docs.astral.sh/uv/). Run these commands from the repository root.

```powershell
# Create the virtual environment and install the core template only.
uv sync

# Install optional flat-file profiling and the test tools.
uv sync --extra profiling --group dev

# Confirm the template is ready to use.
uv run pytest
```

Use the first command for a documentation-only or custom implementation project. Use the second command when profiling CSV, TSV, TXT, or XLSX files, or when running the tests. `uv run` automatically uses the project virtual environment, so no manual activation is required.

Before adding integrations, record the intended outcome, source systems, data ownership, refresh cadence, privacy classification, and approval expectations in project documentation. Add shared Python code under `src/` and repeatable project operations under `scripts/`.

## Local-Only Setup

GitHub is optional. To use this template on a machine without GitHub access, download the template ZIP from a trusted machine, extract it to a stable location such as `C:\Project-Templates\md-data-project-template`, and retain that folder as a clean master copy.

For each new project, copy the master folder to the desired working location and rename it. A ZIP download does not include Git history, so the copy starts as an independent project. Initialize local Git when permitted by your workplace:

```powershell
Copy-Item -Recurse `
   C:\Project-Templates\md-data-project-template `
   C:\Work\DataProjects\my-new-project
cd C:\Work\DataProjects\my-new-project

git init -b main
git add -A
git commit -m "Initial project setup"
```

Run `uv sync --all-extras --dev` and `uv run pytest` in each project copy. When the template changes, download and store a new versioned master copy, such as `md-data-project-template-v1.1`; keep existing projects on their original template version unless they are deliberately upgraded.

## Data Lifecycle

| Location | Purpose |
| --- | --- |
| `data/1_raw/` | Immutable source extracts as received. |
| `data/2_interim/` | Copies or transformations prepared for analysis and downstream work. |
| `data/3_processed/` | Curated, project-approved outputs. |
| `data/4_profiling/` | Descriptive profiling reports for source files. |
| `data/5_spec/` | Reviewable source-to-target Table Specifications. |
| `data/6_semantic/` | Optional reusable semantic-layer exports. |
| `data/7_reconciliation/` | Reconciliation matrices and supporting artifacts. |

Data is ignored by default. Commit only small, non-sensitive sample data when it is essential to reproduce behavior.

## Optional Capabilities

### Source-extract profiling

Invoke [`md-source-extract-profiling`](.github/skills/md-source-extract-profiling/SKILL.md) with `\md-source-extract-profiling` to generate a column-level report for supported flat files. Reports are written to `data/4_profiling/` and do not alter the source file.

### Data contracts and staging

Use [data-contracts/README.md](data-contracts/README.md) when a project needs reviewable source-to-target metadata or a warehouse-style staging layer. Invoke the included [`md-table-spec-builder`](.github/skills/md-table-spec-builder/SKILL.md) skill with `\md-table-spec-builder` to create draft Table Specifications in `data/5_spec/`. It performs no deployment, loading, or platform selection.

### Semantic-layer design

Invoke [`md-semantic-layer-design`](.github/skills/md-semantic-layer-design/SKILL.md) with `\md-semantic-layer-design` after reviewing Table Specifications and business requirements. It creates a platform-independent data model, metric dictionary, and decision log under `references/`, with optional reusable exports under `data/6_semantic/`.

### Reconciliation design

Invoke [`md-reconciliation-design`](.github/skills/md-reconciliation-design/SKILL.md) with `\md-reconciliation-design` when current reports or governed measures must be compared with the proposed semantic layer. It creates a reconciliation plan under `references/` and a comparison matrix in `data/7_reconciliation/`.

### Recommended design sequence

1. Use `\md-source-extract-profiling` to understand source-file structure and quality.
2. Use `\md-table-spec-builder` to create and review source-to-target specifications.
3. Use `\md-semantic-layer-design` to define facts, dimensions, measures, ownership, and model decisions.
4. Use `\md-reconciliation-design` only when existing reports or measures need explicit validation against the proposed semantic layer.
5. Obtain human approval before handing the resulting artifacts to a separate database implementation workflow.

For a business-stakeholder overview of the workflow, its governance model, and adoption benefits, see [Agentic Data Design: Adoption Pitch](agentic-workflow-adoption-pitch.md).

## Examples: Treasury Analytics

The examples below show two complementary Treasury use cases: making today's liquidity process reliable and helping Treasury assess possible future outcomes. Both start with a governed data and semantic foundation; agents assist with validation, investigation, and explanation but do not become the system of record or owner of Treasury definitions.

### Daily Liquidity and Balance Sheet Monitoring

A fictional APAC Corporate and Investment Bank Treasury team receives position, balance-sheet, funding, and high-quality liquid asset extracts each morning. Analysts currently reconcile spreadsheets and assemble a management view manually. The goal is a trusted analytical model that shows the current liquidity position, explains material movements, and surfaces exceptions for Treasury review.

1. Preserve received extracts in `data/1_raw/`, manual reconciliation workbooks in `data/2_interim/`, and the latest report-feeding extracts in `data/3_processed/`. For example:

   ```text
   data/1_raw/liquidity_positions_2026-09-04.csv
   data/1_raw/balance_sheet_2026-09-04.csv
   data/1_raw/funding_positions_2026-09-04.xlsx
   data/1_raw/entity_mapping.xlsx
   ```

2. Record a current-state inventory in `references/current-state-inventory.md`: owner, refresh time, grain, entity and currency coverage, manual adjustments, reconciliation points, report consumers, and known data-quality issues. Map the process from source systems through transformations and reconciliations to the management report and required actions.
3. Invoke `\md-source-extract-profiling` to profile important extracts, such as `data/1_raw/liquidity_positions_2026-09-04.csv`. It creates a descriptive report in `data/4_profiling/1_raw/` without modifying the source file. Invoke `\md-table-spec-builder` with that profiling report to create a draft Table Specification in `data/5_spec/1_raw/`.

4. Review source grain, as-of timestamp, legal entity, currency, product or business line, source identifier, balances, movements, funding type, and liquid-asset classification. Treasury measures must have explicit time, entity, and currency semantics.
5. Invoke `\md-semantic-layer-design` to define approved facts at an agreed position grain and conformed Legal Entity, Currency, Product or Business, Date, and Funding or Liquidity Classification dimensions. Document metric owners, golden sources, reconciliation direction, date logic, exclusions, and report-facing measures such as Total Liquidity Position, Available Liquidity, Liquidity Buffer, Funding Requirement, and daily variance.

The target daily workflow can use specialised agents to check expected feeds and reporting dates; validate schemas, row counts, nulls, duplicates, and unusual values; reconcile key balances; identify material movements by entity, currency, product, funding type, or counterparty; and prepare an evidence-based management summary. Treasury reviews exceptions and material conclusions before publication or action: agents investigate; Treasury decides.

### Liquidity and Balance Sheet Scenario Analysis

A fictional APAC Treasury team uses manually maintained spreadsheets to explore balance-sheet and liquidity stress scenarios. The goal is a governed, reproducible model that separates actual positions, assumptions, scenario logic, and outputs so analysts can test decisions without rebuilding a workbook.

1. Preserve actual positions, funding maturities, deposit profiles, funding rates, and stress-assumption files in `data/1_raw/`. Place existing scenario workbooks in `data/2_interim/` unchanged, and document their scenario names, hardcoded inputs, formulas, overrides, horizons, scopes, and management outputs in `references/`.
2. Profile and specify actuals separately from scenario inputs. Document the provenance and owner of each assumption, and distinguish: actual position, baseline or forecast, scenario assumption, scenario rule, management adjustment, and scenario output.
3. Model the relationships among actual state, scenario inputs, a baseline plan, scenario calculations, and decision-support outputs. Use dimensions such as legal entity, currency, product, funding type, maturity bucket, time horizon, scenario, and assumption version. Keep actual and scenario-derived measures distinct, for example `Liquidity Buffer - Actual` and `Liquidity Buffer - Scenario`.
4. Approve metric definitions for Projected Liquidity Position, Liquidity Buffer, Funding Requirement, Funding Gap, Maturity Gap, Funding Cost Impact, Liquidity Ratio Impact, and change versus baseline. Store model diagrams, metric definitions, mapping decisions, and review records under `references/` or `reports/`.

The target workflow can use agents to validate a structured scenario request, retrieve the latest approved baseline, flag incomplete or conflicting assumptions, calculate the scenario, run sensitivities, explain material drivers, and compare baseline with approved scenarios. When outputs must be proven against current reports, invoke `\md-reconciliation-design` to define the comparison grain, period, tolerance, evidence, and approval record. Treasury owns the assumptions, reviews the evidence, and makes the decision: agents explore the scenario space; Treasury decides.

### Approval and Implementation Handoff

Set Table Specifications to `Reviewed` or `Approved` only after Treasury data owners and report consumers agree on grain, definitions, reconciliation rules, classifications, and semantic-layer measures. The approved specifications and metric definitions are the handoff inputs for a separate database-implementation workflow.

That later workflow selects the platform, creates physical tables, implements transformations, configures connections and credentials, loads data, and publishes reporting assets. This template deliberately does not choose a database, generate deployment code, create connections, or load data.

The `data/` directory is ignored by Git apart from its placeholder files. Keep sensitive or production data out of version control; commit only small, non-sensitive samples when they are necessary to reproduce a decision or test.

## Project Decisions

Before adding implementation detail, document these choices:

- Project outcome: analysis, reporting, engineering, operational integration, or mixed.
- Storage and compute platform, connection approach, and credential management.
- Source systems, ingestion approach, refresh cadence, and retention requirements.
- Modeling approach, including whether to adopt the optional staging convention.
- Data quality, privacy, access-control, and approval expectations.
- Testing, automation, release, and monitoring practices.
- Whether the project requires reproducible sample data.

## Notebooks

Use notebooks for exploration and communication. A light convention is a numeric prefix and concise kebab-case purpose, such as `01-source-exploration.ipynb`.

## Developer Tools

Data Wrangler can be useful for inspecting tabular files. Material Icon Theme and Jupyter Interactive Window shortcuts are optional editor preferences; configure them locally rather than committing shared settings.

## Layout

```text
.github/skills/   Optional Copilot capabilities
data/             Raw, interim, processed, profiling, and specification artifacts
data-contracts/   Guidance for optional source-to-target contracts
notebooks/        Exploratory analysis
references/       Project references and definitions
reports/          Generated deliverables and figures
scripts/          Repeatable project operations
src/              Shared Python code
tests/            Automated checks
```
