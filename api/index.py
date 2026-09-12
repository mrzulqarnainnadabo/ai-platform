"""Vercel entrypoint: preserve the existing host and register intelligence routes."""
from api.original_index import app, handler
from api.intelligence import router as intelligence_router

app.include_router(intelligence_router)

# Extend the existing OpenAPI security decoration to the new authenticated case routes.
_base_openapi = app.openapi


def intelligence_openapi():
    schema = _base_openapi()
    for path, operations in schema.get("paths", {}).items():
        if path.startswith("/api/v1/cases"):
            for operation in operations.values():
                if isinstance(operation, dict):
                    operation["security"] = [{"HTTPBearer": []}]
    return schema


app.openapi = intelligence_openapi  # type: ignore[method-assign]
