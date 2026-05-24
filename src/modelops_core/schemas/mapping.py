"""Mapping-related schemas."""

from __future__ import annotations

from pydantic import Field

from modelops_core.schemas.common import BaseObject


class ValueList(BaseObject):
    """A list of allowed values."""

    watchers: list[str] | None = Field(default=None)


class ValueMapping(BaseObject):
    """Maps values between two ValueLists."""

    value_list: str | None = Field(default=None)


class Mapping(BaseObject):
    """Links source and target FieldEndpoints."""

    source_endpoint: str | None = Field(default=None)
    target_endpoint: str | None = Field(default=None)
    source_value_list: str | None = Field(default=None)
    target_value_list: str | None = Field(default=None)
    value_mapping: str | None = Field(default=None)
    watchers: list[str] | None = Field(default=None)


class MappingSet(BaseObject):
    """A collection of mappings."""

    pass
