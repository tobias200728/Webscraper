"""
Scraper für willhaben.at via httpx (kein Playwright).
- CSRF-Token wird als Cookie von der Homepage gesetzt
- Direkte API-Calls: /webapi/ad-search/search/atz/seo/gebrauchtwagen/auto/{brand}/{model}
"""
import asyncio
import re
import urllib.parse
from typing import AsyncGenerator
import httpx
from app.scrapers.base import BaseScraper
from app.schemas.vehicle import SearchParams, VehicleResult
import logging

logger = logging.getLogger(__name__)

BASE = "https://www.willhaben.at"
SEARCH_API = f"{BASE}/webapi/ad-search/search/atz/seo/gebrauchtwagen/auto"

BRAND_SLUGS = {
    "alfa romeo": "alfa-romeo",
    "mercedes-benz": "mercedes-benz",
    "mercedes": "mercedes-benz",
    "volkswagen": "volkswagen",
    "vw": "volkswagen",
}

# Some models have non-obvious willhaben slugs
MODEL_SLUGS = {
    "3er": "3-series",
    "5er": "5-series",
    "7er": "7-series",
    "x1": "x1", "x3": "x3", "x5": "x5",
    "m3": "m3", "m5": "m5",
    "c-klasse": "c-klasse",
    "e-klasse": "e-klasse",
    "s-klasse": "s-klasse",
    "a-klasse": "a-klasse",
    "b-klasse": "b-klasse",
    "gla": "gla", "glc": "glc", "gle": "gle",
}


def _to_slug(s: str) -> str:
    s = s.lower().strip()
    return BRAND_SLUGS.get(s, s.replace(" ", "-").replace("/", "-"))


def _model_slug(s: str) -> str:
    s = s.lower().strip()
    return MODEL_SLUGS.get(s, s.replace(" ", "-").replace("/", "-"))


class WillhabenScraper(BaseScraper):
    name = "willhaben"
    base_url = BASE

    async def search(self, params: SearchParams) -> AsyncGenerator[VehicleResult, None]:
        brand_slug = _to_slug(params.brand)
        model_slug = _model_slug(params.model)

        # Query params for optional filters
        qp: dict = {}
        if params.max_mileage:
            qp["MILEAGE_TO"] = params.max_mileage
        if params.min_price:
            qp["PRICE_FROM"] = int(params.min_price)
        if params.max_price:
            qp["PRICE_TO"] = int(params.max_price)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "de-AT,de;q=0.9",
            "x-wh-client": "api@willhaben.at;responsive_web;server;1.0.0;desktop",
            "Referer": f"{BASE}/iad/gebrauchtwagen/auto",
        }

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            # Get CSRF token cookie from homepage
            try:
                await client.get(BASE, headers={**headers, "Accept": "text/html"})
                csrf = client.cookies.get("x-bbx-csrf-token")
                if csrf:
                    headers["x-bbx-csrf-token"] = csrf
                    logger.info(f"Willhaben: CSRF token acquired")
                else:
                    logger.warning("Willhaben: No CSRF token in cookies")
            except Exception as e:
                logger.warning(f"Willhaben: Could not fetch homepage: {e}")

            count = 0
            for page in range(1, 4):
                url = f"{SEARCH_API}/{brand_slug}/{model_slug}"
                query = {**qp, "rows": 30, "page": page}
                full_url = f"{url}?{urllib.parse.urlencode(query)}"
                logger.info(f"Willhaben: {full_url}")

                try:
                    resp = await client.get(full_url, headers=headers)
                    resp.raise_for_status()
                except Exception as e:
                    logger.error(f"Willhaben Seite {page}: {e}")
                    break

                data = resp.json()
                ads = data.get("advertSummaryList", {}).get("advertSummary", [])
                rows_found = data.get("rowsFound", 0)
                logger.info(f"Willhaben Seite {page}: {len(ads)} Inserate (total: {rows_found})")

                if not ads:
                    break

                for ad in ads:
                    result = self._parse_ad(ad, params)
                    if result:
                        count += 1
                        yield result

                total_pages = (rows_found + 29) // 30
                if page >= min(total_pages, 3):
                    break

                await asyncio.sleep(0.3)

        logger.info(f"Willhaben: {count} Inserate total")

    def _parse_ad(self, ad: dict, params: SearchParams) -> VehicleResult | None:
        try:
            attrs: dict = {}
            for a in ad.get("attributes", {}).get("attribute", []):
                vals = a.get("values", [])
                attrs[a.get("name", "")] = vals[0] if vals else None

            url_path = attrs.get("SEO_URL") or ""
            if not url_path:
                return None
            listing_url = f"{self.base_url}/{url_path.lstrip('/')}"

            # Images from ALL_IMAGE_URLS (semicolon-separated)
            images = []
            all_img = attrs.get("ALL_IMAGE_URLS") or attrs.get("MMO") or ""
            for ref in all_img.split(";"):
                ref = ref.strip()
                if ref:
                    images.append(f"https://cache.willhaben.at/mmo/{ref}")

            brand = attrs.get("CAR_MODEL/MAKE") or params.brand
            model = attrs.get("CAR_MODEL/MODEL") or params.model
            price = self._safe_float(attrs.get("PRICE/AMOUNT") or attrs.get("PRICE"))
            power_kw = self._safe_int(str(attrs.get("ENGINE/EFFECT") or ""))
            year = self._safe_int(str(attrs.get("YEAR_MODEL") or ""))
            mileage = self._safe_int(str(attrs.get("MILEAGE") or ""))
            fuel = attrs.get("ENGINE/FUEL_RESOLVED") or None
            location = attrs.get("LOCATION") or attrs.get("DISTRICT") or attrs.get("STATE")

            return VehicleResult(
                id=self._make_id(listing_url),
                source=self.name,
                title=attrs.get("HEADING") or ad.get("description") or f"{brand} {model}",
                brand=brand,
                model=model,
                color=None,
                price=price,
                mileage=mileage,
                year=year,
                power_kw=power_kw,
                fuel=fuel,
                location=location,
                image_urls=images[:10],
                listing_url=listing_url,
            )
        except Exception as e:
            logger.debug(f"Willhaben Parse-Fehler: {e}")
            return None
