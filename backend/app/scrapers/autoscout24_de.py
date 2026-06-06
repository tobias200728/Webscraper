"""
Scraper für autoscout24.de mit Österreich-Filter — gleiche Struktur wie .at
"""
import asyncio
import json
import re
import urllib.parse
from typing import AsyncGenerator
import httpx
from app.scrapers.base import BaseScraper
from app.schemas.vehicle import SearchParams, VehicleResult
import logging

logger = logging.getLogger(__name__)


class AutoScout24DeScraper(BaseScraper):
    name = "autoscout24_de"
    base_url = "https://www.autoscout24.de"

    async def search(self, params: SearchParams) -> AsyncGenerator[VehicleResult, None]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "de-AT,de;q=0.9",
        }

        async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
            for page in range(1, 4):
                url = self._build_url(params, page)
                try:
                    resp = await client.get(url)
                    logger.info(f"AutoScout24.de → {resp.status_code} {resp.url}")
                    resp.raise_for_status()
                except Exception as e:
                    logger.error(f"AutoScout24.de Fehler: {e}")
                    break

                listings, num_pages = self._extract(resp.text)
                logger.info(f"AutoScout24.de Seite {page}/{num_pages}: {len(listings)} Inserate")
                if not listings:
                    break

                for item in listings:
                    result = self._parse(item, params)
                    if result:
                        yield result

                if page >= num_pages:
                    break
                await asyncio.sleep(0.5)

    def _build_url(self, params: SearchParams, page: int) -> str:
        brand = params.brand.lower().replace(" ", "-").replace(".", "")
        model = params.model.lower().replace(" ", "-")
        base = f"{self.base_url}/lst/{urllib.parse.quote(brand)}/{urllib.parse.quote(model)}"
        query: dict = {"cy": "A", "atype": "C", "ustate": "N,U"}  # cy=A → Österreich
        if page > 1:
            query["page"] = page
        if params.max_mileage:
            query["kmto"] = params.max_mileage
        if params.min_price:
            query["pricefrom"] = int(params.min_price)
        if params.max_price:
            query["priceto"] = int(params.max_price)
        return f"{base}?{urllib.parse.urlencode(query)}"

    def _extract(self, html: str) -> tuple[list, int]:
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            html, re.DOTALL
        )
        if not match:
            return [], 1
        try:
            data = json.loads(match.group(1))
            pp = data["props"]["pageProps"]
            return pp.get("listings", []), pp.get("numberOfPages", 1)
        except Exception as e:
            logger.error(f"AutoScout24.de Parse-Fehler: {e}")
            return [], 1

    def _parse(self, item: dict, params: SearchParams) -> VehicleResult | None:
        try:
            url = item.get("url", "")
            if url and not url.startswith("http"):
                url = f"{self.base_url}{url}"
            if not url:
                return None

            vehicle = item.get("vehicle", {})
            tracking = item.get("tracking", {})
            price = self._safe_float(str(tracking.get("price", "")))

            year = None
            first_reg = tracking.get("firstRegistration", "")
            if first_reg and "-" in first_reg:
                year = self._safe_int(first_reg.split("-")[-1])

            power_kw = None
            for detail in item.get("vehicleDetails", []):
                if detail.get("iconName") == "speedometer":
                    m = re.search(r"(\d+)\s*kW", detail.get("data", ""))
                    if m:
                        power_kw = int(m.group(1))
                    break

            images = [img for img in item.get("images", []) if isinstance(img, str)]
            loc = item.get("location", {})
            location = loc.get("city") if isinstance(loc, dict) else None

            title = (
                item.get("title")
                or f"{vehicle.get('make', params.brand)} {vehicle.get('model', params.model)}"
                + (f" {vehicle.get('modelVersionInput', '')}".rstrip() if vehicle.get("modelVersionInput") else "")
            ).strip()

            return VehicleResult(
                id=self._make_id(url),
                source=self.name,
                title=title,
                brand=vehicle.get("make") or params.brand,
                model=vehicle.get("model") or params.model,
                color=vehicle.get("colour") or vehicle.get("color"),
                price=price,
                mileage=self._safe_int(str(tracking.get("mileage", ""))),
                year=year,
                power_kw=power_kw,
                fuel=vehicle.get("fuel"),
                location=location,
                image_urls=images[:10],
                listing_url=url,
            )
        except Exception as e:
            logger.debug(f"AutoScout24.de Parse-Fehler: {e}")
            return None
