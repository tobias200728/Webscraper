"""
Scraper für gebrauchtwagen.at
"""
import asyncio
import json
import re
import urllib.parse
from typing import AsyncGenerator
import httpx
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper
from app.schemas.vehicle import SearchParams, VehicleResult
import logging

logger = logging.getLogger(__name__)


class GebrauchtwagenAtScraper(BaseScraper):
    name = "gebrauchtwagen_at"
    base_url = "https://www.gebrauchtwagen.at"

    async def search(self, params: SearchParams) -> AsyncGenerator[VehicleResult, None]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "de-AT,de;q=0.9",
        }

        async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
            # Erst Startseite laden um korrekte URL-Struktur herauszufinden
            url = self._build_url(params, 1)
            try:
                resp = await client.get(url)
                logger.info(f"gebrauchtwagen.at → {resp.status_code} {resp.url}")
                if resp.status_code == 404:
                    # Fallback: Suchseite mit Query-Parametern
                    url = self._build_query_url(params, 1)
                    resp = await client.get(url)
                    logger.info(f"gebrauchtwagen.at Fallback → {resp.status_code} {resp.url}")
                if resp.status_code != 200:
                    return
            except Exception as e:
                logger.error(f"gebrauchtwagen.at Fehler: {e}")
                return

            for page in range(1, 5):
                if page > 1:
                    url = self._build_url(params, page)
                    try:
                        resp = await client.get(url)
                        if resp.status_code != 200:
                            break
                    except Exception:
                        break

                found = list(self._parse_page(resp.text, params))
                logger.info(f"gebrauchtwagen.at Seite {page}: {len(found)} Inserate")
                if not found:
                    break
                for r in found:
                    yield r
                await asyncio.sleep(0.5)

    def _build_url(self, params: SearchParams, page: int) -> str:
        """Versucht die SEO-freundliche URL."""
        brand = params.brand.lower().replace(" ", "-").replace(".", "")
        model = params.model.lower().replace(" ", "-")
        base = f"{self.base_url}/gebrauchtwagen/{urllib.parse.quote(brand)}/{urllib.parse.quote(model)}"
        query: dict = {}
        if page > 1:
            query["seite"] = page
        if params.max_mileage:
            query["kilometer-bis"] = params.max_mileage
        if params.min_price:
            query["preis-von"] = int(params.min_price)
        if params.max_price:
            query["preis-bis"] = int(params.max_price)
        qs = urllib.parse.urlencode(query)
        return f"{base}?{qs}" if qs else base

    def _build_query_url(self, params: SearchParams, page: int) -> str:
        """Fallback: klassische Such-URL mit Query-Parametern."""
        query: dict = {"marke": params.brand, "modell": params.model}
        if page > 1:
            query["seite"] = page
        if params.max_mileage:
            query["kilometer-bis"] = params.max_mileage
        if params.min_price:
            query["preis-von"] = int(params.min_price)
        if params.max_price:
            query["preis-bis"] = int(params.max_price)
        return f"{self.base_url}/gebrauchtwagen/suche?{urllib.parse.urlencode(query)}"

    def _parse_page(self, html: str, params: SearchParams):
        # Versuche __NEXT_DATA__ / __NUXT__ JSON
        for pattern in [
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            r'window\.__NUXT__\s*=\s*(\{.*?\});\s*</script>',
            r'<script[^>]*application/json[^>]*>(.*?)</script>',
        ]:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    items = self._dig_for_listings(data)
                    if items:
                        for item in items:
                            r = self._parse_json_item(item, params)
                            if r:
                                yield r
                        return
                except Exception:
                    continue

        # HTML-Fallback
        yield from self._parse_html(html, params)

    def _dig_for_listings(self, obj, depth=0) -> list:
        if depth > 7 or obj is None:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            keys = set(obj[0].keys())
            if keys & {"price", "mileage", "title", "url", "listingUrl", "id", "preis"}:
                return obj
        if isinstance(obj, dict):
            for key in ("results", "items", "listings", "vehicles", "ads", "data", "fahrzeuge", "inserate"):
                if key in obj:
                    found = self._dig_for_listings(obj[key], depth + 1)
                    if found:
                        return found
            for v in obj.values():
                found = self._dig_for_listings(v, depth + 1)
                if found:
                    return found
        return []

    def _parse_json_item(self, item: dict, params: SearchParams) -> VehicleResult | None:
        try:
            url = item.get("url") or item.get("listingUrl") or item.get("link", "")
            if url and not url.startswith("http"):
                url = f"{self.base_url}{url}"
            if not url:
                return None
            price = item.get("price") or item.get("preis")
            images = item.get("images") or item.get("photos") or item.get("imageUrls") or []
            if images and isinstance(images[0], dict):
                images = [img.get("url") or img.get("src", "") for img in images]
            return VehicleResult(
                id=self._make_id(url),
                source=self.name,
                title=item.get("title") or item.get("name") or f"{params.brand} {params.model}",
                brand=item.get("brand") or item.get("make") or params.brand,
                model=item.get("model") or params.model,
                price=float(price) if price else None,
                mileage=item.get("mileage") or self._safe_int(str(item.get("km", ""))),
                year=item.get("year") or item.get("baujahr"),
                fuel=item.get("fuel") or item.get("kraftstoff"),
                location=item.get("location") or item.get("ort") or item.get("city"),
                image_urls=[i for i in images if isinstance(i, str) and i.startswith("http")][:10],
                listing_url=url,
            )
        except Exception:
            return None

    def _parse_html(self, html: str, params: SearchParams):
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select(
            "article, .listing-item, .car-item, .vehicle-card, "
            "[class*='listing'], [class*='result'], [class*='fahrzeug']"
        )
        for card in cards:
            link = card.select_one("a[href]")
            if not link:
                continue
            href = link["href"]
            if not href or href == "#":
                continue
            url = href if href.startswith("http") else f"{self.base_url}{href}"

            title_el = card.select_one("h2, h3, [class*='title'], [class*='headline']")
            title = title_el.get_text(strip=True) if title_el else f"{params.brand} {params.model}"

            price_el = card.select_one("[class*='price'], [class*='preis']")
            km_el = card.select_one("[class*='km'], [class*='mileage'], [class*='kilomet']")
            year_el = card.select_one("[class*='year'], [class*='jahr'], [class*='erstzulass']")
            loc_el = card.select_one("[class*='location'], [class*='ort'], [class*='standort']")
            images = [
                img.get("data-src") or img.get("src", "")
                for img in card.select("img")
                if (img.get("data-src") or img.get("src", "")).startswith("http")
            ]

            if not title or title == params.brand:
                continue

            yield VehicleResult(
                id=self._make_id(url),
                source=self.name,
                title=title,
                brand=params.brand,
                model=params.model,
                price=self._safe_float(price_el.get_text(strip=True) if price_el else None),
                mileage=self._safe_int(km_el.get_text(strip=True) if km_el else None),
                year=self._safe_int(year_el.get_text(strip=True) if year_el else None),
                location=loc_el.get_text(strip=True) if loc_el else None,
                image_urls=images[:10],
                listing_url=url,
            )
