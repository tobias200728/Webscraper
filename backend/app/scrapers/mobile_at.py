"""
Scraper for mobile.de Austrian listings — large European car marketplace.
Uses the search API endpoint with JSON responses.
"""
import asyncio
from typing import AsyncGenerator
import httpx
from app.scrapers.base import BaseScraper
from app.schemas.vehicle import SearchParams, VehicleResult
import logging

logger = logging.getLogger(__name__)


class MobileAtScraper(BaseScraper):
    name = "mobile_de"
    base_url = "https://www.mobile.de"
    api_url = "https://suchen.mobile.de/fahrzeuge/search.html"

    async def search(self, params: SearchParams) -> AsyncGenerator[VehicleResult, None]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "de-AT,de;q=0.9",
        }

        async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
            for page in range(1, 6):
                query_params = self._build_params(params, page)
                try:
                    resp = await client.get(
                        self.api_url,
                        params=query_params,
                        headers={**headers, "Accept": "application/json, text/javascript"},
                    )
                    resp.raise_for_status()

                    # mobile.de returns JSON when Accept header is set
                    if "application/json" in resp.headers.get("content-type", ""):
                        data = resp.json()
                    else:
                        # Fall back to HTML parsing
                        async for result in self._parse_html(resp.text, params):
                            yield result
                        break

                    items = data.get("items", data.get("ads", []))
                    if not items:
                        break

                    for item in items:
                        result = self._parse_item(item, params)
                        if result:
                            yield result

                    if page >= data.get("totalPages", 1):
                        break

                except Exception as e:
                    self.logger.error(f"mobile.de request failed (page {page}): {e}")
                    break

                await asyncio.sleep(0.4)

    def _build_params(self, params: SearchParams, page: int) -> dict:
        query: dict = {
            "makeModelVariant1.makeId": params.brand.upper(),
            "makeModelVariant1.modelId": params.model,
            "cn": "AT",
            "pageNumber": page,
            "pageSize": 20,
        }
        if params.max_mileage:
            query["maxMileage"] = params.max_mileage
        if params.min_price:
            query["minPrice"] = int(params.min_price)
        if params.max_price:
            query["maxPrice"] = int(params.max_price)
        return query

    def _parse_item(self, item: dict, params: SearchParams) -> VehicleResult | None:
        try:
            listing_id = item.get("id", "")
            listing_url = item.get("url") or f"{self.base_url}/fahrzeugdetails.html?id={listing_id}"
            if not listing_url.startswith("http"):
                listing_url = f"{self.base_url}{listing_url}"

            attrs = item.get("attributes", {})
            price = item.get("price", {}).get("value") or item.get("grossPrice")
            images = [img.get("uri", "") for img in item.get("images", []) if img.get("uri")]

            return VehicleResult(
                id=self._make_id(listing_url),
                source=self.name,
                title=item.get("title") or f"{params.brand} {params.model}",
                brand=attrs.get("make") or params.brand,
                model=attrs.get("model") or params.model,
                color=attrs.get("color"),
                price=float(price) if price else None,
                mileage=attrs.get("mileage"),
                year=attrs.get("firstRegistrationYear"),
                power_kw=attrs.get("powerKw"),
                fuel=attrs.get("fuelType"),
                location=item.get("seller", {}).get("address", {}).get("city"),
                image_urls=images[:10],
                listing_url=listing_url,
            )
        except Exception as e:
            self.logger.debug(f"Failed to parse mobile.de item: {e}")
            return None

    async def _parse_html(self, html: str, params: SearchParams):
        """Fallback HTML parser if JSON endpoint is unavailable."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for article in soup.select("article.cBox-body--resultitem, .result-item"):
            try:
                link = article.select_one("a[href]")
                if not link:
                    continue
                href = link["href"]
                url = href if href.startswith("http") else f"{self.base_url}{href}"

                title_el = article.select_one("h2.title, .result-title, [class*='headline']")
                title = title_el.get_text(strip=True) if title_el else f"{params.brand} {params.model}"

                price_el = article.select_one(".price-block, [class*='price']")
                price_text = price_el.get_text(strip=True) if price_el else None

                mileage_el = article.select_one("[class*='mileage'], [class*='km']")
                mileage_text = mileage_el.get_text(strip=True) if mileage_el else None

                year_el = article.select_one("[class*='year'], [class*='first-registration']")
                year_text = year_el.get_text(strip=True) if year_el else None

                images = [img["src"] for img in article.select("img[src]") if "placeholder" not in img.get("src", "")]

                yield VehicleResult(
                    id=self._make_id(url),
                    source=self.name,
                    title=title,
                    brand=params.brand,
                    model=params.model,
                    price=self._safe_float(price_text),
                    mileage=self._safe_int(mileage_text),
                    year=self._safe_int(year_text),
                    image_urls=images[:10],
                    listing_url=url,
                )
            except Exception as e:
                self.logger.debug(f"Failed to parse mobile.de HTML listing: {e}")
