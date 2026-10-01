# GeoAI Intelligence Architecture

## Purpose

The AI Platform can provide governed geospatial and sustainability intelligence without becoming a GIS application. Geospatial capability is a domain layer above the existing platform kernel.

## Platform boundary

The kernel remains responsible for identity, authorization, capability policy, model/runtime adapters, knowledge and evidence, intelligence cases, auditability, tenant isolation, and human approval boundaries.

The geospatial layer adds provider-neutral contracts for place-aware evidence and spatial operations. It must not bypass the existing governance or case architecture.

## Phase 1 — Domain contracts

The first layer is intentionally lightweight and standard-library only:

- Place
- GeoFeature
- BoundingBox
- SpatialEvidence
- SpatialOperation

These contracts carry CRS, provenance, temporal context, and explicit operation metadata where applicable.

## Phase 2 — Spatial engine

Add an isolated spatial engine using GeoPandas, Shapely, and pyproj when concrete workloads require them.

Initial capabilities:

- point/feature lookup
- bounding-box queries
- intersection
- nearest-feature lookup
- buffers
- spatial aggregation
- CRS transformation

AI agents should invoke governed spatial capabilities rather than generate arbitrary GIS/Python/SQL code.

## Phase 3 — Spatial persistence

Introduce a repository abstraction first. Consider PostGIS only when data volume, concurrent spatial queries, or operational requirements justify it. Do not migrate storage merely because the platform now supports geography.

## Phase 4 — Sustainability intelligence

Add indicator contracts containing:

- indicator definition
- unit
- geographic scope
- temporal scope
- source/provenance
- methodology
- uncertainty or limitations

Indicators should remain evidence-backed and distinguish observed data from model interpretation.

## Place Intelligence

A Place Intelligence case combines a bounded place, spatial evidence, relevant indicators, and governed AI interpretation.

The first demonstrator should be a bounded Nigerian study area rather than a nationwide GIS. Kaduna South is a suitable pilot area because it allows the platform to demonstrate local geographic context without pretending to have complete national coverage.

## Guardrails

- Do not treat AI-generated geographic statements as geographic truth without evidence.
- Preserve CRS and source provenance.
- Keep sensitive location data behind authorization boundaries.
- Do not replace the existing intelligence-case architecture.
- Do not add heavy GIS dependencies at import time unless required.
- Do not introduce PostGIS until an evidence-based workload requires it.
- Keep spatial analysis reproducible and auditable.

## Out of scope for this foundation

- a map-first product redesign
- arbitrary model-generated SQL or Python execution
- nationwide GIS data ingestion
- political candidate ranking or prediction
- replacing the existing AI runtime, governance, or evidence model

## Roadmap

G0: geospatial domain foundation  
G1: governed spatial capabilities  
G2: Place Intelligence cases  
S1: sustainability indicator model  
G3: map/layer visualization  
A1: civic, development, sustainability, ESG, and business location intelligence applications
