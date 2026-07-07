from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    description: str
    unit: str
    served_from_cache: bool
    timestamp: datetime

    class Config:
        from_attributes = True

class PaginatedHistory(BaseModel):
    total: int
    page: int
    limit: int
    items: List[WeatherResponse]