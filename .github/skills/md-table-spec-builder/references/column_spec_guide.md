# Table specification field guide

A Table Specification is an optional source-to-target contract for projects that adopt a staging and warehouse-style architecture. Keep specifications in `data/5_spec/<stage>/`.

| Field | Purpose |
| --- | --- |
| Source Extract | Source file represented by the row. |
| Source Column | Original source column name. |
| Target Table | Proposed destination table. The builder suggests an `stg_` name. |
| Target Column Name | Destination column name, reviewed by a project owner. |
| Type | `Mandatory`, `Optional`, or `Ignore`. |
| Business Role | `Dimension`, `Dimension Attribute`, `Degenerate Dimension`, or `Measure`. |
| Format | Canonical technical format, independent of a platform. |
| Primary/Unique Key | Grain or uniqueness marker, using project-defined vocabulary. |
| PII/Sensitivity | Project-specific data classification. |
| Allowed Values | Optional inclusion rule. |
| Rejected Values | Optional exclusion rule. |
| Description | Business meaning. |
| Notes | Implementation notes and open questions. |
| Status | `Draft`, `Reviewed`, or `Approved`. |

The builder provides deterministic suggestions from profile statistics. Those suggestions are starting points, not decisions. A selected project platform may enforce approved specifications before compiling or loading them.
