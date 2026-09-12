"""Vercel entrypoint: preserve the existing host and register intelligence routes."""
from api.original_index import app, handler
from api.intelligence import router as intelligence_router

app.include_router(intelligence_router)
