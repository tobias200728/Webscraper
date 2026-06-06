from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CORS_ORIGINS: str = "http://localhost:3000"
    SCRAPER_TIMEOUT: int = 30
    MAX_CONCURRENT_SCRAPERS: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
