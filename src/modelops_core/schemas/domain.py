"""Domain-specific canonical object schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from modelops_core.schemas.common import BaseObject


class Attribute(BaseObject):
    """Business meaning — not a physical field."""

    semantic_category: str | None = Field(default=None)
    data_classification: str | None = Field(default=None)
    default_context: str | None = Field(default=None)


class FieldEndpoint(BaseObject):
    """Physical/system representation of a field."""

    system: str | None = Field(default=None)
    endpoint_type: str | None = Field(default=None)
    sap_table: str | None = Field(default=None)
    sap_field: str | None = Field(default=None)
    technical_name: str | None = Field(default=None)
    entity_context: str | None = Field(default=None)
    business_attribute: str | None = Field(default=None)
    value_list: str | None = Field(default=None)


class EntityContext(BaseObject):
    """Business/SAP context in which an attribute is used."""

    context_category: str | None = Field(default=None)
    entity: str | None = Field(default=None)


class AttributeUsage(BaseObject):
    """Links an Attribute to a specific business/SAP context."""

    attribute: str | None = Field(default=None)
    entity_context: str | None = Field(default=None)
    field_endpoint: str | None = Field(default=None)


class System(BaseObject):
    """A system in the landscape."""

    system_type: str | None = Field(default=None)


class MappingSet(BaseObject):
    """A collection of mappings."""

    pass


class Mapping(BaseObject):
    """Links source and target FieldEndpoints."""

    source_endpoint: str | None = Field(default=None)
    target_endpoint: str | None = Field(default=None)
    source_value_list: str | None = Field(default=None)
    target_value_list: str | None = Field(default=None)
    value_mapping: str | None = Field(default=None)


class ValueListEntry(BaseModel):
    """A single entry inside a ValueList."""

    code: str | None = Field(default=None, description="Machine-readable code.")
    label: str | None = Field(default=None, description="Human-readable label.")
    description: str | None = Field(default=None)
    sort_order: int | None = Field(default=None)
    is_default: bool | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class ValueList(BaseObject):
    """A list of allowed values."""

    value_list_type: str | None = Field(default=None, description="e.g. domain, fixed, custom.")
    parent_value_list: str | None = Field(default=None)
    entries: list[ValueListEntry] | None = Field(default=None)


class ValueMappingEntry(BaseModel):
    """A single mapping between two value codes."""

    source_code: str | None = Field(default=None)
    target_code: str | None = Field(default=None)
    fallback: bool | None = Field(default=None)
    description: str | None = Field(default=None)


class ValueMapping(BaseObject):
    """Maps values between two ValueLists."""

    value_list: str | None = Field(default=None)
    source_value_list: str | None = Field(default=None)
    target_value_list: str | None = Field(default=None)
    entries: list[ValueMappingEntry] | None = Field(default=None)


class ValidationRule(BaseObject):
    """Checks expected correctness."""

    rule_type: str | None = Field(default=None)
    attribute: str | None = Field(default=None)


class BusinessRule(BaseObject):
    """Business rule."""

    attribute: str | None = Field(default=None)


class DataQualityCheck(BaseObject):
    """Data quality check."""

    attribute: str | None = Field(default=None)


class OwnershipRole(BaseObject):
    """Ownership role."""

    attribute: str | None = Field(default=None)


class TransformationLogic(BaseObject):
    """Transformation logic."""

    mapping: str | None = Field(default=None)


class MasterDataDomain(BaseObject):
    """Master data domain."""

    pass


class MigrationObject(BaseObject):
    """Migration object."""

    domain: str | None = Field(default=None)


class BusinessEntity(BaseObject):
    """Business entity."""

    domain: str | None = Field(default=None)
    entity_context: str | None = Field(default=None)


class SystemEnvironment(BaseObject):
    """System environment."""

    system: str | None = Field(default=None)


class SAPObject(BaseObject):
    """SAP object."""

    pass


class Interface(BaseObject):
    """Interface."""

    system: str | None = Field(default=None)


class Dataset(BaseObject):
    """Dataset."""

    system: str | None = Field(default=None)


class Person(BaseObject):
    """Person."""

    email: str | None = Field(default=None)


class Team(BaseObject):
    """Team."""

    pass


class Evidence(BaseObject):
    """Evidence supporting a decision."""

    pass
