from abc import ABC, abstractmethod
from typing import List, AsyncGenerator
from app.schemas.vehicle import SearchParams, VehicleResult
import logging
import uuid

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all vehicle scrapers. Each scraper must implement search()."""

    name: str = "base"
    base_url: str = ""

    def __init__(self):
        self.logger = logging.getLogger(f"scraper.{self.name}")

    @abstractmethod
    async def search(self, params: SearchParams) -> AsyncGenerator[VehicleResult, None]:
        """Yield VehicleResult objects one by one as they are found."""
        ...

    def _make_id(self, url: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, url))

    def _safe_int(self, value: str | None) -> int | None:
        if not value:
            return None
        cleaned = "".join(c for c in str(value) if c.isdigit())
        return int(cleaned) if cleaned else None

    def _safe_float(self, value: str | None) -> float | None:
        if not value:
            return None
        cleaned = "".join(c for c in str(value) if c.isdigit() or c in ".,")
        cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None
