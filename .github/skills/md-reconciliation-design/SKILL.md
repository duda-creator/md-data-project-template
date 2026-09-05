---
name: md-reconciliation-design
description: Use when designing a reviewable reconciliation plan between current reports or metrics and a proposed semantic layer.
---

# Reconciliation design

Use this optional skill when existing reports, certified upstream measures, or regulated metrics must be compared with a proposed data model and semantic layer. It creates a reviewable validation contract; it does not execute reconciliations, select a platform, load data, or publish reports.

## Inputs

Review the project evidence before drafting the reconciliation artifacts:

- `references/current-state-inventory.md` for current report sources and manual adjustments.
- `references/data-model.md` and `references/metric-dictionary.csv` for the proposed model and semantic definitions.
- Existing report definitions, reconciliations, and supporting evidence under `references/` or `reports/`.
- Relevant Table Specifications in `data/5_spec/` when source lineage or grain requires clarification.

Do not infer acceptable tolerances, expected differences, ownership, or sign-off. Record missing information as an open item.

## Create or update artifacts

1. Create or update `references/reconciliation-plan.md`, using [reconciliation_plan_template.md](references/reconciliation_plan_template.md), to document scope, comparison approach, evidence, investigation process, approvals, and exclusions.
2. Create or update `data/7_reconciliation/reconciliation-matrix.csv`, using [reconciliation_matrix_template.csv](references/reconciliation_matrix_template.csv), with one row per current-to-proposed metric comparison.

## Design rules

- State the existing report or metric and its authoritative source separately from the proposed semantic metric.
- Define comparison direction, grain, reporting period or as-of date rule, filters, and exclusions for every comparison.
- Use a numeric tolerance only when a named owner has approved it. Explain expected differences rather than treating them as unexplained breaks.
- Keep observed metric reconciliations separate from scenario-derived metric validations.
- Use `Draft`, `Reviewed`, and `Approved` statuses. A row cannot be `Approved` without an owner, comparison rule, tolerance or documented zero-tolerance rule, and evidence location.
- Preserve approved comparisons; add a new row or superseding plan entry when their logic changes.

## Review outcome

Summarize comparison coverage, incomplete controls, expected differences, evidence gaps, and required sign-offs. A completed plan is an input to the later implementation and testing workflow.