"""Core domain contracts for governed geospatial intelligence.

These models deliberately avoid heavyweight GIS dependencies. Spatial engines can
consume these contracts later without coupling the platform kernel to one vendor
or geometry implementation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class BoundingBox:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        if self.min_x > self.max_x:
            raise ValueError("min_x must be <= max_x")
        if self.min_y > self.max_y:
            raise ValueError("min_y must be <= max_y")


@dataclass(frozen=True)
class Place:
    name: str
    country_code: str | None = None
    admin_level: str | None = None
    external_id: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("place name must not be empty")


@dataclass(frozen=True)
class GeoFeature:
    geometry_type: str
    coordinates: Any
    crs: str
    properties: Mapping[str, Any] = field(default_factory=dict)
    source: str = ""
    observed_at: datetime | None = None

    def __post_init__(self) -> None:
        allowed = {
            "Point",
            "MultiPoint",
            "LineString",
            "MultiLineString",
            "Polygon",
            "MultiPolygon",
            "GeometryCollection",
        }
        if self.geometry_type not in allowed:
            raise ValueError(f"unsupported geometry type: {self.geometry_type}")
        if not self.crs.strip():
            raise ValueError("crs must not be empty")
        if not self.source.strip():
            raise ValueError("source must not be empty")


@dataclass(frozen=True)
class SpatialEvidence:
    evidence_id: str
    feature: GeoFeature
    description: str
    source_uri: str | None = None
    confidence_note: str | None = None

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be empty")
        if not self.description.strip():
            raise ValueError("description must not be empty")


@dataclass(frozen=True)
class SpatialOperation:
    operation: str
    inputs: tuple[str, ...]
    parameters: Mapping[str, Any] = field(default_factory=dict)
    engine: str | None = None

    def __post_init__(self) -> None:
        if not self.operation.strip():
            raise ValueError("operation must not be empty")
        if not self.inputs:
            raise ValueError("inputs must not be empty")
