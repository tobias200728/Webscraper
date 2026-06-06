"""
Scraper für autoscout24.at — liest Inserate aus __NEXT_DATA__.props.pageProps.listings
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


class AutoScout24Scraper(BaseScraper):
    name = "autoscout24"
    base_url = "https://www.autoscout24.at"

    async def search(self, params: SearchParams) -> AsyncGenerator[VehicleResult, None]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-AT,de;q=0.9",
        }

        async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
            for page in range(1, 6):
                url = self._build_url(params, page)
                try:
                    resp = await client.get(url)
                    logger.info(f"AutoScout24 → {resp.status_code} {resp.url}")
                    resp.raise_for_status()
                except Exception as e:
                    logger.error(f"AutoScout24 Fehler: {e}")
                    break

                listings, num_pages = self._extract(resp.text)
                logger.info(f"AutoScout24 Seite {page}/{num_pages}: {len(listings)} Inserate")

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
        query: dict = {"cy": "A", "atype": "C", "ustate": "N,U"}
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
            page_props = data["props"]["pageProps"]
            return page_props.get("listings", []), page_props.get("numberOfPages", 1)
        except Exception as e:
            logger.error(f"AutoScout24 Parse-Fehler: {e}")
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

            # Preis aus tracking (immer numerisch)
            price = self._safe_float(str(tracking.get("price", "")))

            # Jahr aus tracking.firstRegistration z.B. "12-2015" → 2015
            year = None
            first_reg = tracking.get("firstRegistration", "")
            if first_reg and "-" in first_reg:
                year = self._safe_int(first_reg.split("-")[-1])

            # Kraftstoff direkt aus vehicle.fuel
            fuel = vehicle.get("fuel")

            # Kilometerstand aus tracking (numerisch)
            mileage = self._safe_int(str(tracking.get("mileage", "")))

            # Leistung aus vehicleDetails (iconName == "speedometer") → "110 kW (150 PS)"
            power_kw = None
            for detail in item.get("vehicleDetails", []):
                if detail.get("iconName") == "speedometer":
                    kw_match = re.search(r"(\d+)\s*kW", detail.get("data", ""))
                    if kw_match:
                        power_kw = int(kw_match.group(1))
                    break

            # Bilder sind einfache URL-Strings
            images = [img for img in item.get("images", []) if isinstance(img, str)]

            # Standort
            loc = item.get("location", {})
            location = loc.get("city") if isinstance(loc, dict) else None

            # Titel aus vehicle-Feldern zusammenbauen wenn kein expliziter Titel
            title = (
                item.get("title")
                or f"{vehicle.get('make', params.brand)} {vehicle.get('model', params.model)}"
                + (f" {vehicle.get('modelVersionInput', '')}".rstrip() if vehicle.get("modelVersionInput") else "")
            )

            return VehicleResult(
                id=self._make_id(url),
                source=self.name,
                title=title.strip(),
                brand=vehicle.get("make") or params.brand,
                model=vehicle.get("model") or params.model,
                color=vehicle.get("colour") or vehicle.get("color"),
                price=price,
                mileage=mileage,
                year=year,
                power_kw=power_kw,
                fuel=fuel,
                location=location,
                image_urls=images[:10],
                listing_url=url,
            )
        except Exception as e:
            logger.debug(f"AutoScout24 Parse-Fehler: {e}")
            return None
