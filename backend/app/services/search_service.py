"""Orchestriert alle Scraper parallel und streamt die Ergebnisse."""
import asyncio
import statistics
import logging
from typing import List, AsyncGenerator
from app.scrapers import ALL_SCRAPERS
from app.schemas.vehicle import SearchParams, VehicleResult
from app.config import settings

logger = logging.getLogger(__name__)


def _rate_prices(results: List[VehicleResult]) -> None:
    """Bewertet Preise relativ zueinander (in-place)."""
    prices = [r.price for r in results if r.price and r.price > 0]
    if len(prices) < 3:
        return
    median = statistics.median(prices)
    stdev = statistics.stdev(prices) if len(prices) > 1 else median * 0.15
    for r in results:
        if not r.price:
            continue
        diff = r.price - median
        if diff < -stdev * 0.5:
            r.price_rating = "cheap"
        elif diff > stdev * 0.5:
            r.price_rating = "expensive"
        else:
            r.price_rating = "average"


async def search_vehicles(params: SearchParams) -> AsyncGenerator[VehicleResult, None]:
    """Startet alle Scraper gleichzeitig und yieldet Ergebnisse sobald sie ankommen."""
    active = params.sources or list(ALL_SCRAPERS.keys())
    sem = asyncio.Semaphore(settings.MAX_CONCURRENT_SCRAPERS)
    all_results: List[VehicleResult] = []
    seen_ids: set[str] = set()

    async def run(name: str) -> tuple[str, List[VehicleResult]]:
        async with sem:
            scraper = ALL_SCRAPERS[name]()
            found = []
            try:
                async for vehicle in scraper.search(params):
                    found.append(vehicle)
            except Exception as e:
                logger.warning(f"Scraper {name} Fehler: {e}")
            return name, found

    tasks = [asyncio.create_task(run(name)) for name in active if name in ALL_SCRAPERS]

    for coro in asyncio.as_completed(tasks):
        name, results = await coro
        for r in results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                all_results.append(r)
                yield r

    # Preisbewertung nachträglich — wird beim nächsten SSE-Flush nicht mehr gesendet,
    # aber der "done"-Event enthält die aktualisierten Bewertungen falls nötig.
    _rate_prices(all_results)
