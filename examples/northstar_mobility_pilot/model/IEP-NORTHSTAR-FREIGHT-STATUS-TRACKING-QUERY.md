---
id: IEP-NORTHSTAR-FREIGHT-STATUS-TRACKING-QUERY
type: InterfaceEndpoint
status: active
schema_version: '1.0'
name: Tracking Query Operation
created_at: '2026-07-25T09:00:00+00:00'
domain: DOMAIN-LOGISTICS
interface: IFACE-NORTHSTAR-FREIGHT-STATUS
system: SYS-FREIGHTLINK-TMS
endpoint_type: api_operation
protocol: https_json
method: GET
path: /freight/v1/tracking-events
request_message_type: MSG-NORTHSTAR-TRACKING-QUERY-REQUEST
response_message_types:
- MSG-NORTHSTAR-TRACKING-EVENT
message_exchange_pattern: request_response
description: Returns tracking events for a shipment known to Freightlink TMS.
---

# Tracking Query Operation

Returns tracking events for a shipment known to Freightlink TMS.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.
