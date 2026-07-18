---
id: VMAP-MATERIAL-TYPE-LEGACY-TO-S4
type: ValueMapping
status: active
schema_version: '1.0'
name: Material Type Legacy-to-S/4 Value Mapping
created_at: '2026-01-19T09:00:00+00:00'
domain: DOMAIN-MATERIAL
source_value_list: VLIST-LEGACY-MATERIAL-TYPES
target_value_list: VLIST-S4-MATERIAL-TYPES
business_owner: PERSON-SUPPLIER-STEWARD
technical_owner: PERSON-SUPPLIER-STEWARD
entries:
- source_code: VH
  target_code: VEH
  description: Legacy vehicle to Vehicle.
- source_code: SV
  target_code: SERV
  description: Legacy service to Service.
- source_code: PT
  target_code: PART
  description: Legacy part to Spare Part.
- source_code: PK
  target_code: PKG
  description: Legacy package to Service Package.
description: Value-level conversion from Voyager material types to S/4HANA types. Codes outside the legacy
  list (and bogus pre-converted S/4 codes) are tracked in ISS-MATERIAL-INVALID-TYPE-CODES.
---

# Material Type Legacy-to-S/4 Value Mapping

Value-level conversion from Voyager material types to S/4HANA types. Codes outside the legacy list (and bogus pre-converted S/4 codes) are tracked in ISS-MATERIAL-INVALID-TYPE-CODES.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.
