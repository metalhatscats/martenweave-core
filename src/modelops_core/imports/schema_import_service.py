"""Governed schema-to-proposal import for local machine-readable contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops_core.imports.schema_inspection import (
    NormalizedSchemaDocument,
    NormalizedSchemaField,
    inspect_schema_file,
)
from modelops_core.patching.patch_model import PatchOperation
from modelops_core.patching.patch_proposal_service import (
    build_patch_proposal,
    render_patch_proposal_markdown,
    write_patch_proposal,
)
from modelops_core.patching.patch_validator import validate_patch_proposal
from modelops_core.reports.source_registry_service import SourceRegistryService
from modelops_core.schemas.source_registry import SourceEntry
from modelops_core.validation.result import ValidationSeverity

_NON_ALNUM = re.compile(r"[^A-Z0-9]+")


@dataclass(frozen=True)
class SchemaImportResult:
    proposal: dict[str, Any]
    proposal_markdown: str
    validation_errors: int
    validation_warnings: int
    source_id: str
    inspected: NormalizedSchemaDocument


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sanitize_segment(value: str) -> str:
    upper = value.upper()
    cleaned = _NON_ALNUM.sub("-", upper).strip("-")
    return cleaned or "UNKNOWN"


def _proposal_id(document: NormalizedSchemaDocument) -> str:
    return f"PP-SCHEMA-{document.checksum[:16].upper()}"


def _source_id(document: NormalizedSchemaDocument) -> str:
    return f"SCHEMA-{document.checksum[:16].upper()}"


def _entity_id(document: NormalizedSchemaDocument, entity_name: str) -> str:
    return (
        f"ENTITY-SCHEMA-{_sanitize_segment(document.source_identity)}-"
        f"{_sanitize_segment(entity_name)}"
    )


def _attribute_id(document: NormalizedSchemaDocument, field: NormalizedSchemaField) -> str:
    return (
        f"ATTR-SCHEMA-{_sanitize_segment(document.source_identity)}-"
        f"{_sanitize_segment(field.field_path)}"
    )


def _field_endpoint_id(document: NormalizedSchemaDocument, field: NormalizedSchemaField) -> str:
    return (
        f"FEP-SCHEMA-{_sanitize_segment(document.source_identity)}-"
        f"{_sanitize_segment(field.field_path)}"
    )


def _value_list_id(document: NormalizedSchemaDocument, field: NormalizedSchemaField) -> str:
    return (
        f"VLIST-SCHEMA-{_sanitize_segment(document.source_identity)}-"
        f"{_sanitize_segment(field.field_path)}"
    )


def _interface_id(document: NormalizedSchemaDocument) -> str:
    return f"IFACE-SCHEMA-{_sanitize_segment(document.source_identity)}"


def _interface_endpoint_id(document: NormalizedSchemaDocument, operation_id: str) -> str:
    return (
        f"IEP-SCHEMA-{_sanitize_segment(document.source_identity)}-"
        f"{_sanitize_segment(operation_id)}"
    )


def _message_type_id(document: NormalizedSchemaDocument, message_name: str) -> str:
    return (
        f"MSG-SCHEMA-{_sanitize_segment(document.source_identity)}-"
        f"{_sanitize_segment(message_name)}"
    )


def _schema_node_id(document: NormalizedSchemaDocument, field_path: str) -> str:
    return (
        f"SNODE-SCHEMA-{_sanitize_segment(document.source_identity)}-"
        f"{_sanitize_segment(field_path)}"
    )


def _schema_field_endpoint_type(document: NormalizedSchemaDocument) -> str:
    endpoint_types = {
        "openapi": "openapi_schema_field",
        "json_schema": "json_schema_property",
        "json_payload": "json_payload_field",
        "cds_metadata_export": "cds_metadata_field",
        "idoc_payload": "idoc_segment_field",
        "we60_html_documentation": "we60_documentation_field",
        "integration_suite_package": "integration_suite_resource",
        "xml_payload": "xml_payload_field",
        "field_catalog": "field_catalog_column",
        "sap_mapping_workbook": "sap_mapping_field",
        "sap_migration_cockpit_template": "sap_migration_cockpit_field",
        "edmx": "edmx_property",
        "wsdl": "wsdl_message_field",
        "xsd": "xsd_element",
    }
    return endpoint_types.get(document.source_format, "schema_field")


def _source_evidence(document: NormalizedSchemaDocument) -> str:
    warning_text = "; ".join(document.warnings[:5]) if document.warnings else "none"
    return (
        f"Schema import evidence from {Path(document.source_path).name} "
        f"({document.source_format}, checksum {document.checksum}, "
        f"parser {document.parser_version}, inspected {_now_iso()}). "
        f"Warnings: {warning_text}."
    )


def _entity_operations(document: NormalizedSchemaDocument) -> list[PatchOperation]:
    operations: list[PatchOperation] = []
    seen_entities: set[str] = set()
    for entity in document.entities:
        object_id = _entity_id(document, entity.name)
        if object_id in seen_entities:
            continue
        seen_entities.add(object_id)
        operations.append(
            PatchOperation(
                op="create_object",
                object_id=object_id,
                object_type="BusinessEntity",
                after={
                    "id": object_id,
                    "type": "BusinessEntity",
                    "status": "draft",
                    "name": entity.name,
                    "description": entity.description
                    or f"Imported from {document.source_format} schema evidence.",
                },
                reason=f"Entity imported from {entity.source_evidence}.",
            )
        )
    if not operations and document.source_identity:
        fallback_id = _entity_id(document, document.source_identity)
        operations.append(
            PatchOperation(
                op="create_object",
                object_id=fallback_id,
                object_type="BusinessEntity",
                after={
                    "id": fallback_id,
                    "type": "BusinessEntity",
                    "status": "draft",
                    "name": document.source_identity,
                    "description": f"Imported from {document.source_format} schema evidence.",
                },
                reason="Fallback root entity imported from schema identity.",
            )
        )
    return operations


def _field_operations(document: NormalizedSchemaDocument) -> list[PatchOperation]:
    operations: list[PatchOperation] = []
    created_value_lists: set[str] = set()
    for field in document.fields:
        entity_name = field.entity_name or document.source_identity
        entity_id = _entity_id(document, entity_name)
        attr_id = _attribute_id(document, field)
        fep_id = _field_endpoint_id(document, field)

        operations.append(
            PatchOperation(
                op="create_object",
                object_id=attr_id,
                object_type="Attribute",
                after={
                    "id": attr_id,
                    "type": "Attribute",
                    "status": "draft",
                    "name": field.field_path.split(".")[-1].replace("[]", ""),
                    "entity": entity_id,
                    "description": field.description
                    or f"Imported attribute for {field.field_path}.",
                },
                reason=f"Attribute imported from {field.source_evidence}.",
            )
        )

        value_list_id: str | None = None
        if field.enumerations:
            value_list_id = _value_list_id(document, field)
            if value_list_id not in created_value_lists:
                created_value_lists.add(value_list_id)
                operations.append(
                    PatchOperation(
                        op="create_object",
                        object_id=value_list_id,
                        object_type="ValueList",
                        after={
                            "id": value_list_id,
                            "type": "ValueList",
                            "status": "draft",
                            "name": f"{field.field_path} values",
                            "value_list_type": "enum",
                            "entries": [
                                {"code": value, "label": value} for value in field.enumerations
                            ],
                            "description": f"Imported enumeration for {field.field_path}.",
                        },
                        reason=f"Enumeration imported from {field.source_evidence}.",
                    )
                )

        operations.append(
            PatchOperation(
                op="create_object",
                object_id=fep_id,
                object_type="FieldEndpoint",
                after={
                    "id": fep_id,
                    "type": "FieldEndpoint",
                    "status": "draft",
                    "name": field.field_path,
                    "endpoint_type": _schema_field_endpoint_type(document),
                    "technical_name": field.field_path,
                    "business_attribute": attr_id,
                    "value_list": value_list_id,
                    "description": f"Imported schema field from {field.source_evidence}.",
                },
                reason=f"FieldEndpoint imported from {field.source_evidence}.",
            )
        )
    return operations


def _message_role_by_entity(document: NormalizedSchemaDocument) -> dict[str, str]:
    roles: dict[str, set[str]] = {}
    for operation in document.operations:
        if operation.request_body_schema:
            roles.setdefault(operation.request_body_schema, set()).add("request")
        for response in operation.response_schemas:
            schema_name = response.get("schema")
            if schema_name:
                roles.setdefault(schema_name, set()).add("response")
    resolved: dict[str, str] = {}
    for entity_name in {entity.name for entity in document.entities} | set(roles):
        entity_roles = roles.get(entity_name, set())
        if entity_roles == {"request"}:
            resolved[entity_name] = "request"
        elif entity_roles == {"response"}:
            resolved[entity_name] = "response"
        elif entity_roles == {"request", "response"}:
            resolved[entity_name] = "request_response"
        elif document.source_format in {"json_payload", "xml_payload", "idoc_payload"}:
            resolved[entity_name] = "payload"
        else:
            resolved[entity_name] = "schema"
    return resolved


def _interface_root_operations(document: NormalizedSchemaDocument) -> list[PatchOperation]:
    if document.source_format not in {
        "openapi",
        "wsdl",
        "integration_flow_artifact",
        "integration_suite_package",
    }:
        return []

    interface_id = _interface_id(document)
    source_label_map = {
        "openapi": "OpenAPI",
        "wsdl": "WSDL",
        "integration_flow_artifact": "Integration Flow",
        "integration_suite_package": "Integration Suite Package",
    }
    source_label = source_label_map[document.source_format]
    return [
        PatchOperation(
            op="create_object",
            object_id=interface_id,
            object_type="Interface",
            after={
                "id": interface_id,
                "type": "Interface",
                "status": "draft",
                "name": document.source_identity,
                "description": (
                    f"Imported {source_label} interface from {Path(document.source_path).name}."
                ),
            },
            reason=f"Interface imported from {source_label} evidence.",
        )
    ]


def _interface_endpoint_operations(document: NormalizedSchemaDocument) -> list[PatchOperation]:
    if document.source_format not in {
        "openapi",
        "wsdl",
        "integration_flow_artifact",
        "integration_suite_package",
    }:
        return []

    operations: list[PatchOperation] = []
    interface_id = _interface_id(document)
    endpoint_type_map = {
        "openapi": "openapi_operation",
        "wsdl": "wsdl_operation",
        "integration_flow_artifact": "integration_flow_operation",
        "integration_suite_package": "integration_flow_operation",
    }
    endpoint_type = endpoint_type_map[document.source_format]
    for operation in document.operations:
        endpoint_id = _interface_endpoint_id(document, operation.operation_id)
        request_message_type = (
            _message_type_id(document, operation.request_body_schema)
            if operation.request_body_schema
            else None
        )
        response_message_types = [
            _message_type_id(document, response["schema"])
            for response in operation.response_schemas
            if response.get("schema")
        ]
        operations.append(
            PatchOperation(
                op="create_object",
                object_id=endpoint_id,
                object_type="InterfaceEndpoint",
                after={
                    "id": endpoint_id,
                    "type": "InterfaceEndpoint",
                    "status": "draft",
                    "name": operation.operation_id,
                    "interface": interface_id,
                    "endpoint_type": endpoint_type,
                    "protocol": operation.protocol,
                    "method": operation.method,
                    "path": operation.path,
                    "request_message_type": request_message_type,
                    "response_message_types": response_message_types or None,
                    "parameters": operation.parameters or None,
                    "message_exchange_pattern": (
                        "request_response"
                        if response_message_types
                        else "one_way" if request_message_type else "notification"
                    ),
                    "description": operation.description
                    or f"{operation.method} {operation.path}",
                },
                reason=f"Interface endpoint imported from {operation.source_evidence}.",
            )
        )
    return operations


def _message_type_operations(document: NormalizedSchemaDocument) -> list[PatchOperation]:
    entity_names = [entity.name for entity in document.entities]
    if not entity_names and document.fields:
        entity_names = sorted(
            {field.entity_name or document.source_identity for field in document.fields}
        )
    if not entity_names:
        return []

    interface_id = (
        _interface_id(document)
        if document.source_format
        in {"openapi", "wsdl", "integration_flow_artifact", "integration_suite_package"}
        else None
    )
    protocol = document.source_format
    roles = _message_role_by_entity(document)
    operations: list[PatchOperation] = []
    for entity_name in sorted(dict.fromkeys(entity_names)):
        message_id = _message_type_id(document, entity_name)
        operations.append(
            PatchOperation(
                op="create_object",
                object_id=message_id,
                object_type="MessageType",
                after={
                    "id": message_id,
                    "type": "MessageType",
                    "status": "draft",
                    "name": entity_name,
                    "interface": interface_id,
                    "protocol": protocol,
                    "message_role": roles.get(entity_name, "schema"),
                    "description": (
                        f"Imported message structure for {entity_name} from "
                        f"{Path(document.source_path).name}."
                    ),
                },
                reason=f"MessageType imported for entity '{entity_name}'.",
            )
        )
    return operations


def _schema_node_operations(document: NormalizedSchemaDocument) -> list[PatchOperation]:
    operations: list[PatchOperation] = []
    created_value_lists: set[str] = set()
    for field in document.fields:
        entity_name = field.entity_name or document.source_identity
        node_id = _schema_node_id(document, field.field_path)
        parent_node_id = (
            _schema_node_id(document, field.parent_path)
            if field.parent_path
            else None
        )
        attr_id = _attribute_id(document, field)
        fep_id = _field_endpoint_id(document, field)
        value_list_id = _value_list_id(document, field) if field.enumerations else None
        node_after: dict[str, Any] = {
            "id": node_id,
            "type": "SchemaNode",
            "status": "draft",
            "name": field.field_path.split(".")[-1].replace("[]", ""),
            "message_type": _message_type_id(document, entity_name),
            "parent_node": parent_node_id,
            "business_attribute": attr_id,
            "field_endpoint": fep_id,
            "value_list": value_list_id,
            "technical_name": field.field_path,
            "data_type": field.data_type,
            "required": field.required,
            "cardinality": field.cardinality,
            "description": field.description
            or f"Imported schema node for {field.field_path}.",
        }
        operations.append(
            PatchOperation(
                op="create_object",
                object_id=node_id,
                object_type="SchemaNode",
                after=node_after,
                reason=f"SchemaNode imported from {field.source_evidence}.",
            )
        )
        if value_list_id and value_list_id not in created_value_lists:
            created_value_lists.add(value_list_id)
    return operations


def _build_operations(document: NormalizedSchemaDocument) -> list[PatchOperation]:
    return [
        *_entity_operations(document),
        *_field_operations(document),
        *_interface_root_operations(document),
        *_message_type_operations(document),
        *_schema_node_operations(document),
        *_interface_endpoint_operations(document),
    ]


def _affected_objects(operations: list[PatchOperation]) -> list[str]:
    affected: list[str] = []
    seen: set[str] = set()
    for operation in operations:
        if operation.object_id and operation.object_id not in seen:
            seen.add(operation.object_id)
            affected.append(operation.object_id)
    return affected


def inspect_to_proposal(path: Path) -> SchemaImportResult:
    """Inspect a schema file and build a deterministic proposal artifact."""
    document = inspect_schema_file(path)
    operations = _build_operations(document)
    proposal = build_patch_proposal(
        proposal_id=_proposal_id(document),
        operations=operations,
        affected_objects=_affected_objects(operations),
        source_evidence=_source_evidence(document),
        created_by="system",
        generated_by="schema_import",
    )
    validation_results = validate_patch_proposal(proposal)
    proposal["validation_status"] = (
        "invalid"
        if any(result.severity == ValidationSeverity.ERROR for result in validation_results)
        else "valid"
    )
    proposal["validation_results"] = [result.model_dump() for result in validation_results]
    proposal["title"] = f"Schema Import Proposal: {document.source_identity}"

    validation_errors = sum(
        1 for result in validation_results if result.severity == ValidationSeverity.ERROR
    )
    validation_warnings = sum(
        1 for result in validation_results if result.severity == ValidationSeverity.WARNING
    )
    return SchemaImportResult(
        proposal=proposal,
        proposal_markdown=render_patch_proposal_markdown(proposal),
        validation_errors=validation_errors,
        validation_warnings=validation_warnings,
        source_id=_source_id(document),
        inspected=document,
    )


def write_schema_proposal(
    result: SchemaImportResult,
    *,
    repo_model_path: Path,
    output_path: Path | None = None,
) -> Path:
    """Write the schema-import proposal artifact."""
    if output_path is None:
        return write_patch_proposal(result.proposal, repo_model_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.proposal_markdown, encoding="utf-8")
    return output_path


def register_schema_import_source(
    service: SourceRegistryService,
    result: SchemaImportResult,
    *,
    source_url: str | None = None,
    license_note: str | None = None,
    usage_note: str | None = None,
) -> str:
    """Register schema-import evidence in the source registry."""
    captured_at = _now_iso()
    entry = SourceEntry(
        source_id=result.source_id,
        source_type="schema_import",
        display_name=f"Schema import: {Path(result.inspected.source_path).name}",
        file_path=result.inspected.source_path,
        file_hash=result.inspected.checksum,
        registered_at=captured_at,
        last_seen_at=captured_at,
        status="ok" if result.validation_errors == 0 else "warning",
        metadata={
            "source_format": result.inspected.source_format,
            "source_version": result.inspected.source_version,
            "namespace": result.inspected.namespace,
            "parser_version": result.inspected.parser_version,
            "checksum": result.inspected.checksum,
            "retrieved_at": captured_at,
            "source_url": source_url,
            "license_note": license_note,
            "usage_note": usage_note,
            "entity_count": len(result.inspected.entities),
            "field_count": len(result.inspected.fields),
            "operation_count": len(result.inspected.operations),
            "proposal_id": result.proposal["id"],
            "validation_errors": result.validation_errors,
            "validation_warnings": result.validation_warnings,
        },
    )
    return service.register(entry)
