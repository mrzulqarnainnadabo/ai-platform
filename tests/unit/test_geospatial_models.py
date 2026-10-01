from datetime import datetime, timezone

import pytest

from ai_platform.geospatial import (
    BoundingBox,
    GeoFeature,
    Place,
    SpatialEvidence,
    SpatialOperation,
)


def test_bounding_box_requires_valid_axis_order():
    assert BoundingBox(1, 2, 3, 4).max_x == 3
    with pytest.raises(ValueError):
        BoundingBox(3, 2, 1, 4)
    with pytest.raises(ValueError):
        BoundingBox(1, 4, 3, 2)


def test_place_requires_name():
    assert Place("Kaduna South", country_code="NG").country_code == "NG"
    with pytest.raises(ValueError):
        Place("   ")


def test_geo_feature_requires_supported_geometry_crs_and_source():
    feature = GeoFeature(
        geometry_type="Point",
        coordinates=[7.4, 10.5],
        crs="EPSG:4326",
        source="example-dataset",
        observed_at=datetime.now(timezone.utc),
    )
    assert feature.geometry_type == "Point"

    with pytest.raises(ValueError):
        GeoFeature("Circle", [], "EPSG:4326", source="example")
    with pytest.raises(ValueError):
        GeoFeature("Point", [], "", source="example")
    with pytest.raises(ValueError):
        GeoFeature("Point", [], "EPSG:4326", source="")


def test_spatial_evidence_requires_identity_and_description():
    feature = GeoFeature("Point", [7.4, 10.5], "EPSG:4326", source="survey")
    evidence = SpatialEvidence("ev-1", feature, "Observed feature")
    assert evidence.evidence_id == "ev-1"

    with pytest.raises(ValueError):
        SpatialEvidence("", feature, "Observed feature")
    with pytest.raises(ValueError):
        SpatialEvidence("ev-1", feature, "")


def test_spatial_operation_requires_operation_and_inputs():
    operation = SpatialOperation(
        operation="intersects",
        inputs=("place:1", "feature:1"),
        parameters={"predicate": "within"},
        engine="future-spatial-engine",
    )
    assert operation.inputs == ("place:1", "feature:1")

    with pytest.raises(ValueError):
        SpatialOperation("", ("place:1",))
    with pytest.raises(ValueError):
        SpatialOperation("intersects", ())
