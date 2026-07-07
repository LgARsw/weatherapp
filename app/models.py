from sqlalchemy import String, DateTime, Float, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base

class WeatherQuery(Base):
    __tablename__ = "weather_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    city: Mapped[str] = mapped_column(String, index=True)
    temperature: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String)
    unit: Mapped[str] = mapped_column(String(1))  # 'C' or 'F'
    served_from_cache: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)