"""Vercel entrypoint: preserve the existing host and register intelligence routes."""
from fastapi import Response

from api.original_index import app, handler
from api.intelligence import router as intelligence_router
from api.cases_frontend import cases_page

app.include_router(intelligence_router)

# The case workspace is a browser shell only; authentication and authorization
# happen through Supabase Auth + the protected /api/v1/cases API.


@app.get("/app/cases", include_in_schema=False)
def intelligence_cases_app() -> Response:
    return cases_page()


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
