import json
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.vehicle import SearchParams
from app.services.search_service import search_vehicles
from app.scrapers import ALL_SCRAPERS

router = APIRouter(prefix="/search", tags=["search"])
logger = logging.getLogger(__name__)


@router.get("/sources")
async def get_sources():
    return {"sources": list(ALL_SCRAPERS.keys())}


@router.post("/stream")
async def stream_search(params: SearchParams):
    """Streamt Suchergebnisse als Server-Sent Events — ein Fahrzeug pro Event."""
    count = 0

    async def event_generator():
        nonlocal count
        try:
            async for vehicle in search_vehicles(params):
                count += 1
                yield f"data: {vehicle.model_dump_json()}\n\n"
        except Exception as e:
            logger.error(f"Stream-Fehler: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield f"event: done\ndata: {json.dumps({'total': count})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )
