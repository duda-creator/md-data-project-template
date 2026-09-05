# Optional Data Contracts

Adopt this workflow when a project benefits from a reviewable contract between source extracts and a warehouse-style staging layer. It is optional: projects may use the core template without specifications or a staging architecture.

## Workflow

1. Place immutable extracts in `data/1_raw/`.
2. Create an analysis-ready copy in `data/2_interim/` when preparation is needed.
3. Optionally profile the source and retain the report in `data/4_profiling/`.
4. Create or extend a Table Specification in `data/5_spec/`.
5. Use `\md-semantic-layer-design` to create a data model, metric dictionary, and decision log from reviewed specifications.
6. Optionally use `\md-reconciliation-design` to define how current reports or governed metrics will be compared with the proposed semantic layer.
7. Review the specifications, semantic artifacts, and reconciliation plan with data owners and set their statuses according to project governance.
8. After approval and platform selection, implement the project-specific compilation, deployment, and load steps that consume the approved artifacts.

## Staging Convention

The optional builder proposes target names beginning with `stg_`. This keeps the landing layer distinguishable from curated models, but projects may change the convention before implementation.

## Contract Boundary

A Table Specification captures provenance, target names, requiredness, canonical formats, business roles, key markers, sensitivity, descriptions, and review status. The semantic-layer design artifacts define facts, dimensions, measures, ownership, and model decisions. The optional reconciliation artifacts define evidence and acceptance criteria for comparing existing and proposed metrics. None of these artifacts choose a storage platform, compile definitions, establish connections, or move data.

The project-specific implementation decides whether `Approved` is required before downstream actions. The template permits revising an approved specification so each project can adopt the governance level it needs.
