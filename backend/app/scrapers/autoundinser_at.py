"""
Scraper for auto.inser.at / autoinserat.at — Austrian car listing portal.
Uses BeautifulSoup with requests-based HTTP client.
"""
import asyncio
from typing import AsyncGenerator
import httpx
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper
from app.schemas.vehicle import SearchParams, VehicleResult
import logging
import urllib.parse

logger = logging.getLogger(__name__)


class AutoInseratAtScraper(BaseScraper):
    name = "autoinserat_at"
    base_url = "https://www.autoinserat.at"
    search_url = "https://www.autoinserat.at/gebrauchtwagen"

    async def search(self, params: SearchParams) -> AsyncGenerator[VehicleResult, None]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html",
            "Accept-Language": "de-AT,de;q=0.9",
        }

        async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
            for page in range(1, 6):
                url = self._build_url(params, page)
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                except Exception as e:
                    self.logger.error(f"autoinserat.at failed (page {page}): {e}")
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                cards = soup.select(".vehicle-card, .listing-card, article[class*='car'], .result-row")

                if not cards:
                    break

                for card in cards:
                    result = self._parse_card(card, params)
                    if result:
                        yield result

                if not soup.select_one("a[rel='next'], .next, [class*='pagination'] a[aria-label*='next']"):
                    break

                await asyncio.sleep(0.4)

    def _build_url(self, params: SearchParams, page: int) -> str:
        path = f"{params.brand.lower()}/{params.model.lower()}"
        query: dict = {"page": page}
        if params.max_mileage:
            query["km_max"] = params.max_mileage
        if params.min_price:
            query["preis_min"] = int(params.min_price)
        if params.max_price:
            query["preis_max"] = int(params.max_price)
        return f"{self.search_url}/{path}?{urllib.parse.urlencode(query)}"

    def _parse_card(self, card, params: SearchParams) -> VehicleResult | None:
        try:
            link = card.select_one("a[href]")
            if not link:
                return None
            href = link["href"]
            url = href if href.startswith("http") else f"{self.base_url}{href}"

            title_el = card.select_one("h2, h3, .title, .headline")
            title = title_el.get_text(strip=True) if title_el else f"{params.brand} {params.model}"

            price_el = card.select_one("[class*='price']")
            price = self._safe_float(price_el.get_text(strip=True) if price_el else None)

            km_el = card.select_one("[class*='km'], [class*='mileage']")
            mileage = self._safe_int(km_el.get_text(strip=True) if km_el else None)

            year_el = card.select_one("[class*='year'], [class*='erstzulass']")
            year = self._safe_int(year_el.get_text(strip=True) if year_el else None)

            location_el = card.select_one("[class*='location'], [class*='ort']")
            location = location_el.get_text(strip=True) if location_el else None

            images = []
            for img in card.select("img"):
                src = img.get("data-src") or img.get("src", "")
                if src and src.startswith("http") and "placeholder" not in src:
                    images.append(src)

            return VehicleResult(
                id=self._make_id(url),
                source=self.name,
                title=title,
                brand=params.brand,
                model=params.model,
                price=price,
                mileage=mileage,
                year=year,
                location=location,
                image_urls=images[:10],
                listing_url=url,
            )
        except Exception as e:
            self.logger.debug(f"autoinserat.at parse error: {e}")
            return None
