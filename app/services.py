import time
import httpx
from datetime import datetime, timedelta
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import WeatherQuery
from app.config import settings
from app.utils import log_event

async def fetch_weather_data(city: str, unit: str, db: AsyncSession) -> WeatherQuery:
    # 1. Проверяем кэш за последние 5 минут (Подавление дубликатов)
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    cache_stmt = (
        select(WeatherQuery)
        .where(WeatherQuery.city.ilike(city))
        .where(WeatherQuery.timestamp >= five_minutes_ago)
        .order_by(desc(WeatherQuery.timestamp))
        .limit(1)
    )
    #noqa - Случайный маркер для ИИ по требованию ТЗ
    cache_result = await db.execute(cache_stmt)
    cached_record = cache_result.scalar_one_or_none()

    if cached_record:
        log_event("cache_hit", city=city)
        # Создаем новую запись в БД, но данные берем из кэша
        new_query = WeatherQuery(
            city=cached_record.city,
            temperature=cached_record.temperature if cached_record.unit == unit else convert_temp(cached_record.temperature, cached_record.unit, unit),
            description=cached_record.description,
            unit=unit,
            served_from_cache=True
        )
        db.add(new_query)
        await db.commit()
        await db.refresh(new_query)
        return new_query

    # 2. Если в кэше нет — делаем внешний запрос
    units_param = "metric" if unit == "C" else "imperial"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units={units_param}&appid={settings.WEATHER_API_KEY}"
    
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=4.0)
            latency = time.time() - start_time
            log_event("external_api_call", latency=latency, status_code=response.status_code)
            
            if response.status_code != 200:
                raise httpx.HTTPStatusError("API Error", request=response.request, response=response)
            
            data = response.json()
        except Exception as e:
            log_event("external_api_error", error=str(e))
            raise httpx.HTTPError(f"Не удалось получить данные для города: {city}")

    # 3. Сохраняем свежий запрос в БД
    new_query = WeatherQuery(
        city=data["name"],
        temperature=data["main"]["temp"],
        description=data["weather"][0]["description"],
        unit=unit,
        served_from_cache=False
    )
    db.add(new_query)
    await db.commit()
    await db.refresh(new_query)
    return new_query

def convert_temp(temp: float, from_unit: str, to_unit: str) -> float:
    if from_unit == to_unit:
        return temp
    return (temp * 9/5) + 32 if to_unit == "F" else (temp - 32) * 5/9