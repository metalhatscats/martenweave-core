---
id: ISS-MATERIAL-INVALID-TYPE-CODES
type: Issue
status: open
schema_version: '1.0'
name: Material extract contains invalid type codes
created_at: '2026-02-02T09:00:00+00:00'
title: Material extract contains invalid type codes
domain: DOMAIN-MATERIAL
priority: medium
issue_type: data_quality
attribute: ATTR-MATERIAL-TYPE
related_objects:
- DS-VOYAGER-MATERIALS
- VLIST-S4-MATERIAL-TYPES
- VMAP-MATERIAL-TYPE-LEGACY-TO-S4
business_owner: PERSON-GOVERNANCE-REVIEWER
description: voyager_materials.csv ships an unmodeled s4_material_type column containing values FQ, ZZ,
  and QQ that are not in VLIST-S4-MATERIAL-TYPES and have no entry in VMAP-MATERIAL-TYPE-LEGACY-TO-S4.
  Rows must be quarantined or the value list extended before load.
---

# Material extract contains invalid type codes

voyager_materials.csv ships an unmodeled s4_material_type column containing values FQ, ZZ, and QQ that are not in VLIST-S4-MATERIAL-TYPES and have no entry in VMAP-MATERIAL-TYPE-LEGACY-TO-S4. Rows must be quarantined or the value list extended before load.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.
