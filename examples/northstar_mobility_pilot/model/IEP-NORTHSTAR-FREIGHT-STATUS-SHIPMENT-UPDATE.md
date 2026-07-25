---
id: IEP-NORTHSTAR-FREIGHT-STATUS-SHIPMENT-UPDATE
type: InterfaceEndpoint
status: active
schema_version: '1.0'
name: Shipment Status Update Operation
created_at: '2026-07-25T09:00:00+00:00'
domain: DOMAIN-LOGISTICS
interface: IFACE-NORTHSTAR-FREIGHT-STATUS
system: SYS-FREIGHTLINK-TMS
endpoint_type: api_operation
protocol: https_json
method: POST
path: /freight/v1/shipment-status
request_message_type: MSG-NORTHSTAR-SHIPMENT-STATUS-REQUEST
response_message_types:
- MSG-NORTHSTAR-SHIPMENT-STATUS-RESPONSE
message_exchange_pattern: request_response
description: Receives a shipment status update from Freightlink TMS and returns a processing
  acknowledgement.
---

# Shipment Status Update Operation

Receives a shipment status update from Freightlink TMS and returns a processing acknowledgement.

Synthetic pilot object for the fictional Northstar Mobility Group; all names, systems, and data are invented and contain no real information.
