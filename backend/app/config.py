from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://*.vercel.app"]
    SCRAPER_TIMEOUT: int = 30
    MAX_CONCURRENT_SCRAPERS: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
