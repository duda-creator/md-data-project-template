---
name: md-semantic-layer-design
description: Use when designing a platform-independent data model and semantic layer from reviewed table specifications and business requirements.
---

# Semantic-layer design

Use this skill after source profiling and Table Specification review to create a reviewable business model and metric contract. It does not select a platform, generate transformations, create database objects, load data, or publish reports.

## Inputs

Review the available project evidence before drafting artifacts:

- `data/5_spec/` for reviewed or approved Table Specifications.
- `data/4_profiling/` for profiling evidence when a specification is incomplete.
- `references/current-state-inventory.md` for source ownership, current reports, manual adjustments, and data-quality concerns.
- Existing metric definitions, report documentation, and stakeholder requirements under `references/` or `reports/`.

Treat generated Table Specification suggestions as inputs, not decisions. Ask for missing business context rather than inferring a fact grain, relationship, metric formula, ownership, or approval status.

## Create or update artifacts

Create the following project-level artifacts. Preserve existing approved content and record proposed changes as drafts or open decisions.

1. `references/data-model.md`, using [data_model_template.md](references/data_model_template.md), with facts, dimensions, declared grain, business keys, relationships and cardinality, time behavior, conformance, lineage, and open questions.
2. `references/metric-dictionary.csv`, using [metric_dictionary_template.csv](references/metric_dictionary_template.csv), with one row per proposed or approved semantic metric.
3. `references/model-decisions.md`, using [model_decisions_template.md](references/model_decisions_template.md), as an append-only decision log.

Optionally place reusable semantic exports in `data/6_semantic/`; do not put source data or platform-specific code there.

## Design rules

- Declare each fact's grain before defining measures or relationships.
- Define conformed dimensions and business-key behavior before mapping report measures.
- Make time semantics explicit: as-of date, effective date, reporting period, time zone, and snapshot or transaction behavior as applicable.
- Keep observed and scenario-derived metrics distinct.
- For each metric, document its owner, authoritative source classification, derivation, aggregation, evaluation grain, date rule, filters, exclusions, and reconciliation method.
- Use `Draft`, `Reviewed`, and `Approved` statuses. Only set `Approved` after the named business owner confirms the definition.
- Record unresolved choices in the decision log rather than silently choosing a design.

## Review outcome

Summarize the created or updated artifacts, assumptions, open decisions, and the people who must review them. Approved model and metric artifacts are inputs to a separate implementation workflow.