from pydantic import BaseModel, field_validator
from typing import List, Optional


class SearchParams(BaseModel):
    brand: str
    model: str
    color: Optional[str] = None
    max_mileage: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    sources: Optional[List[str]] = None

    @field_validator("brand", "model")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Darf nicht leer sein")
        return v.strip()


class VehicleResult(BaseModel):
    id: str
    source: str
    title: str
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    price: Optional[float] = None
    mileage: Optional[int] = None
    year: Optional[int] = None
    power_kw: Optional[int] = None
    fuel: Optional[str] = None
    location: Optional[str] = None
    image_urls: List[str] = []
    listing_url: str
    price_rating: Optional[str] = None  # "cheap" | "average" | "expensive"
