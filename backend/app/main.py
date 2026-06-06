from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.api.routes.search import router as search_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="CarFinder Austria API",
    description="Aggregierte Gebrauchtwagen-Suche für österreichische Portale",
    version="2.0.0",
)

import json as _json

def _parse_origins(raw: str) -> list:
    raw = raw.strip()
    if raw.startswith("["):
        return _json.loads(raw)
    return [o.strip() for o in raw.split(",")]

cors_origins = _parse_origins(settings.CORS_ORIGINS)
allow_all = cors_origins == ["*"] or "*" in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
