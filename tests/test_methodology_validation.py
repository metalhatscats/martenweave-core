"""Tests for methodology validation rules (issue #26)."""

from __future__ import annotations

from modelops_core.repository import ParsedObject
from modelops_core.validation.pipeline import validate_objects
from modelops_core.validation.result import ValidationSeverity


def _obj(frontmatter: dict, source_path: str = "test.md") -> ParsedObject:
    return ParsedObject(
        source_path=source_path,
        content_hash="abc123",
        frontmatter=frontmatter,
        body="",
        parser_error=None,
    )


class TestFieldEndpointMissingAttribute:
    def test_warns_when_no_attribute_or_usage(self) -> None:
        fe = _obj(
            {
                "id": "FEP-TEST-1",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "Field 1",
            }
        )
        summary = validate_objects([fe])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ATTRIBUTE"]
        assert len(warns) == 1
        assert warns[0].severity == ValidationSeverity.WARNING
        assert "FEP-TEST-1" in warns[0].message

    def test_no_warning_with_attribute(self) -> None:
        attr = _obj(
            {
                "id": "ATTR-TEST-1",
                "type": "Attribute",
                "status": "active",
                "name": "Attr",
            }
        )
        fe = _obj(
            {
                "id": "FEP-TEST-1",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "Field 1",
                "attribute": "ATTR-TEST-1",
            }
        )
        summary = validate_objects([attr, fe])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ATTRIBUTE"]
        assert len(warns) == 0

    def test_no_warning_with_business_attribute(self) -> None:
        attr = _obj(
            {
                "id": "ATTR-TEST-1",
                "type": "Attribute",
                "status": "active",
                "name": "Attr",
            }
        )
        fe = _obj(
            {
                "id": "FEP-TEST-1",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "Field 1",
                "business_attribute": "ATTR-TEST-1",
            }
        )
        summary = validate_objects([attr, fe])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ATTRIBUTE"]
        assert len(warns) == 0

    def test_no_warning_with_attribute_usage(self) -> None:
        fe = _obj(
            {
                "id": "FEP-TEST-1",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "Field 1",
            }
        )
        usage = _obj(
            {
                "id": "AU-TEST-1",
                "type": "AttributeUsage",
                "status": "active",
                "field_endpoint": "FEP-TEST-1",
            }
        )
        summary = validate_objects([fe, usage])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ATTRIBUTE"]
        assert len(warns) == 0

    def test_no_warning_for_archived(self) -> None:
        fe = _obj(
            {
                "id": "FEP-TEST-1",
                "type": "FieldEndpoint",
                "status": "archived",
                "name": "Field 1",
            }
        )
        summary = validate_objects([fe])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ATTRIBUTE"]
        assert len(warns) == 0


class TestFlatModelStructure:
    def test_warns_when_many_fields_no_contexts(self) -> None:
        objects: list[ParsedObject] = [
            _obj(
                {
                    "id": "BE-1",
                    "type": "BusinessEntity",
                    "status": "active",
                    "name": "Entity",
                }
            ),
        ]
        for i in range(12):
            objects.append(
                _obj(
                    {
                        "id": f"FEP-{i:02d}",
                        "type": "FieldEndpoint",
                        "status": "active",
                        "name": f"Field {i}",
                    }
                )
            )
        summary = validate_objects(objects)
        warns = [r for r in summary.results if r.code == "FLAT_MODEL_STRUCTURE"]
        assert len(warns) == 1
        assert warns[0].severity == ValidationSeverity.WARNING
        assert "12" in warns[0].message

    def test_no_warning_when_contexts_present(self) -> None:
        objects: list[ParsedObject] = [
            _obj(
                {
                    "id": "BE-1",
                    "type": "BusinessEntity",
                    "status": "active",
                    "name": "Entity",
                }
            ),
            _obj(
                {
                    "id": "EC-1",
                    "type": "EntityContext",
                    "status": "active",
                    "name": "Context",
                }
            ),
        ]
        for i in range(12):
            objects.append(
                _obj(
                    {
                        "id": f"FEP-{i:02d}",
                        "type": "FieldEndpoint",
                        "status": "active",
                        "name": f"Field {i}",
                    }
                )
            )
        summary = validate_objects(objects)
        warns = [r for r in summary.results if r.code == "FLAT_MODEL_STRUCTURE"]
        assert len(warns) == 0

    def test_no_warning_when_few_fields(self) -> None:
        objects: list[ParsedObject] = [
            _obj(
                {
                    "id": "BE-1",
                    "type": "BusinessEntity",
                    "status": "active",
                    "name": "Entity",
                }
            ),
        ]
        for i in range(5):
            objects.append(
                _obj(
                    {
                        "id": f"FEP-{i:02d}",
                        "type": "FieldEndpoint",
                        "status": "active",
                        "name": f"Field {i}",
                    }
                )
            )
        summary = validate_objects(objects)
        warns = [r for r in summary.results if r.code == "FLAT_MODEL_STRUCTURE"]
        assert len(warns) == 0

    def test_no_warning_when_no_business_entities(self) -> None:
        objects: list[ParsedObject] = []
        for i in range(12):
            objects.append(
                _obj(
                    {
                        "id": f"FEP-{i:02d}",
                        "type": "FieldEndpoint",
                        "status": "active",
                        "name": f"Field {i}",
                    }
                )
            )
        summary = validate_objects(objects)
        warns = [r for r in summary.results if r.code == "FLAT_MODEL_STRUCTURE"]
        assert len(warns) == 0


class TestAttributeMissingContext:
    def test_warns_when_no_context_in_enterprise_model(self) -> None:
        attr = _obj(
            {
                "id": "ATTR-1",
                "type": "Attribute",
                "status": "active",
                "name": "Attr",
            }
        )
        ec = _obj(
            {
                "id": "EC-1",
                "type": "EntityContext",
                "status": "active",
                "name": "Context",
            }
        )
        summary = validate_objects([attr, ec])
        warns = [r for r in summary.results if r.code == "ATTRIBUTE_MISSING_CONTEXT"]
        assert len(warns) == 1
        assert warns[0].severity == ValidationSeverity.WARNING

    def test_no_warning_with_context(self) -> None:
        attr = _obj(
            {
                "id": "ATTR-1",
                "type": "Attribute",
                "status": "active",
                "name": "Attr",
                "entity_context": "EC-1",
            }
        )
        ec = _obj(
            {
                "id": "EC-1",
                "type": "EntityContext",
                "status": "active",
                "name": "Context",
            }
        )
        summary = validate_objects([attr, ec])
        warns = [r for r in summary.results if r.code == "ATTRIBUTE_MISSING_CONTEXT"]
        assert len(warns) == 0

    def test_no_warning_when_no_contexts_in_model(self) -> None:
        attr = _obj(
            {
                "id": "ATTR-1",
                "type": "Attribute",
                "status": "active",
                "name": "Attr",
            }
        )
        summary = validate_objects([attr])
        warns = [r for r in summary.results if r.code == "ATTRIBUTE_MISSING_CONTEXT"]
        assert len(warns) == 0

    def test_no_warning_for_archived(self) -> None:
        attr = _obj(
            {
                "id": "ATTR-1",
                "type": "Attribute",
                "status": "archived",
                "name": "Attr",
            }
        )
        ec = _obj(
            {
                "id": "EC-1",
                "type": "EntityContext",
                "status": "active",
                "name": "Context",
            }
        )
        summary = validate_objects([attr, ec])
        warns = [r for r in summary.results if r.code == "ATTRIBUTE_MISSING_CONTEXT"]
        assert len(warns) == 0


class TestFieldEndpointMissingEnrichment:
    def test_warns_when_no_lov_in_model_with_lovs(self) -> None:
        fe = _obj(
            {
                "id": "FEP-1",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "Field",
            }
        )
        vl = _obj(
            {
                "id": "VL-1",
                "type": "ValueList",
                "status": "active",
                "name": "List",
            }
        )
        summary = validate_objects([fe, vl])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ENRICHMENT"]
        assert len(warns) == 1
        assert "value_list" in warns[0].message

    def test_no_warning_with_lov(self) -> None:
        fe = _obj(
            {
                "id": "FEP-1",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "Field",
                "value_list": "VL-1",
            }
        )
        vl = _obj(
            {
                "id": "VL-1",
                "type": "ValueList",
                "status": "active",
                "name": "List",
            }
        )
        summary = validate_objects([fe, vl])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ENRICHMENT"]
        assert len(warns) == 0

    def test_warns_when_not_mapped_in_model_with_mappings(self) -> None:
        fe = _obj(
            {
                "id": "FEP-1",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "Field",
            }
        )
        mapping = _obj(
            {
                "id": "MAP-1",
                "type": "Mapping",
                "status": "active",
                "name": "Map",
                "source_endpoint": "FEP-OTHER",
                "target_endpoint": "FEP-OTHER2",
            }
        )
        summary = validate_objects([fe, mapping])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ENRICHMENT"]
        assert len(warns) == 1
        assert "mapping" in warns[0].message

    def test_no_warning_when_mapped(self) -> None:
        fe = _obj(
            {
                "id": "FEP-1",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "Field",
            }
        )
        mapping = _obj(
            {
                "id": "MAP-1",
                "type": "Mapping",
                "status": "active",
                "name": "Map",
                "source_endpoint": "FEP-1",
                "target_endpoint": "FEP-2",
            }
        )
        summary = validate_objects([fe, mapping])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ENRICHMENT"]
        assert len(warns) == 0

    def test_warns_when_attr_has_no_rule_in_model_with_rules(self) -> None:
        attr = _obj(
            {
                "id": "ATTR-1",
                "type": "Attribute",
                "status": "active",
                "name": "Attr",
            }
        )
        fe = _obj(
            {
                "id": "FEP-1",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "Field",
                "attribute": "ATTR-1",
            }
        )
        vr = _obj(
            {
                "id": "VR-1",
                "type": "ValidationRule",
                "status": "active",
                "name": "Rule",
                "attribute": "ATTR-OTHER",
            }
        )
        summary = validate_objects([attr, fe, vr])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ENRICHMENT"]
        assert len(warns) == 1
        assert "validation_rule" in warns[0].message

    def test_no_warning_when_attr_has_rule(self) -> None:
        attr = _obj(
            {
                "id": "ATTR-1",
                "type": "Attribute",
                "status": "active",
                "name": "Attr",
            }
        )
        fe = _obj(
            {
                "id": "FEP-1",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "Field",
                "attribute": "ATTR-1",
            }
        )
        vr = _obj(
            {
                "id": "VR-1",
                "type": "ValidationRule",
                "status": "active",
                "name": "Rule",
                "attribute": "ATTR-1",
            }
        )
        summary = validate_objects([attr, fe, vr])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ENRICHMENT"]
        assert len(warns) == 0

    def test_no_warning_when_model_has_no_enrichment_objects(self) -> None:
        fe = _obj(
            {
                "id": "FEP-1",
                "type": "FieldEndpoint",
                "status": "active",
                "name": "Field",
            }
        )
        summary = validate_objects([fe])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ENRICHMENT"]
        assert len(warns) == 0

    def test_no_warning_for_archived(self) -> None:
        fe = _obj(
            {
                "id": "FEP-1",
                "type": "FieldEndpoint",
                "status": "archived",
                "name": "Field",
            }
        )
        vl = _obj(
            {
                "id": "VL-1",
                "type": "ValueList",
                "status": "active",
                "name": "List",
            }
        )
        summary = validate_objects([fe, vl])
        warns = [r for r in summary.results if r.code == "FIELD_ENDPOINT_MISSING_ENRICHMENT"]
        assert len(warns) == 0


class TestSimpleTableModeNotPunished:
    """Simple table mode: Domain → Entity → Attribute → FieldEndpoint
    with no EntityContext, AttributeUsage, or parent_entity.
    """

    def test_simple_model_no_false_positives(self) -> None:
        objects = [
            _obj(
                {
                    "id": "DOMAIN-PROD",
                    "type": "MasterDataDomain",
                    "status": "active",
                    "name": "Product",
                }
            ),
            _obj(
                {
                    "id": "BE-PROD",
                    "type": "BusinessEntity",
                    "status": "active",
                    "name": "Product",
                    "domain": "DOMAIN-PROD",
                }
            ),
            _obj(
                {
                    "id": "ATTR-NAME",
                    "type": "Attribute",
                    "status": "active",
                    "name": "Name",
                    "domain": "DOMAIN-PROD",
                }
            ),
            _obj(
                {
                    "id": "FEP-NAME",
                    "type": "FieldEndpoint",
                    "status": "active",
                    "name": "Name",
                    "attribute": "ATTR-NAME",
                }
            ),
        ]
        summary = validate_objects(objects)
        methodology_warns = [
            r
            for r in summary.results
            if r.code
            in (
                "FLAT_MODEL_STRUCTURE",
                "ATTRIBUTE_MISSING_CONTEXT",
                "FIELD_ENDPOINT_MISSING_ENRICHMENT",
                "FIELD_ENDPOINT_MISSING_ATTRIBUTE",
            )
        ]
        assert len(methodology_warns) == 0
