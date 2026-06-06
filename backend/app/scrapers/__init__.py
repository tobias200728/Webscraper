from app.scrapers.willhaben import WillhabenScraper
from app.scrapers.autoscout24 import AutoScout24Scraper
from app.scrapers.autoscout24_de import AutoScout24DeScraper

ALL_SCRAPERS = {
    "willhaben": WillhabenScraper,
    "autoscout24": AutoScout24Scraper,
    "autoscout24_de": AutoScout24DeScraper,
}

__all__ = ["ALL_SCRAPERS", "WillhabenScraper", "AutoScout24Scraper", "AutoScout24DeScraper"]
