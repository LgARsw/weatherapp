import io
import csv
from datetime import datetime
from fastapi import FastAPI, Depends, Query, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import get_db, engine
from app.models import WeatherQuery
from app.schemas import WeatherResponse, PaginatedHistory
from app.services import fetch_weather_data
from app.utils import rate_limiter, log_event
from app.config import settings
app = FastAPI(title="Weather History Web App")
templates = Jinja2Templates(directory="templates")
@app.middleware("http")
async def log_requests(request: Request, call_next):
    log_event("request_start", path=request.url.path, method=request.method)
    start_time = datetime.utcnow()
    try:
        response = await call_next(request)
        process_time = (datetime.utcnow() - start_time).total_seconds()
        log_event("request_end", path=request.url.path, duration=process_time, status_code=response.status_code)
        return response
    except Exception as e:
        log_event("request_error", path=request.url.path, error=str(e))
        raise

# Вспомогательная функция для построения фильтрованного запроса к истории
def build_history_query(city: Optional[str], date_from: Optional[datetime], date_to: Optional[datetime]):
    stmt = select(WeatherQuery).order_by(desc(WeatherQuery.timestamp))
    if city:
        stmt = stmt.where(WeatherQuery.city.ilike(f"%{city}%"))
    if date_from:
        stmt = stmt.where(WeatherQuery.timestamp >= date_from)
    if date_to:
        stmt = stmt.where(WeatherQuery.timestamp <= date_to)
    return stmt

@app.get("/weather", response_model=WeatherResponse)
async def get_weather(
    city: str, 
    unit: str = Query("C", regex="^[CF]$"), 
    request: Request = None, 
    db: AsyncSession = Depends(get_db)
):
    client_ip = request.client.host if request and request.client else "127.0.0.1"
    if not rate_limiter.is_allowed(client_ip):
        log_event("rate_limit_exceeded", ip=client_ip)
        raise HTTPException(status_code=429, detail="Слишком много запросов. Пожалуйста, подождите минуту.")
    
    try:
        record = await fetch_weather_data(city, unit, db)
        return record
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/history", response_model=PaginatedHistory)
async def get_history(
    city: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    stmt = build_history_query(city, date_from, date_to)
    
    # Считаем общее кол-во записей для пагинации
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_core()

    # Применяем смещение
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {"total": total, "page": page, "limit": limit, "items": items}

@app.get("/history/export")
async def export_history(
    city: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = build_history_query(city, date_from, date_to)
    result = await db.execute(stmt)
    items = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "City", "Temperature", "Unit", "Description", "Served From Cache", "Timestamp"])

    for item in items:
        writer.writerow([item.id, item.city, item.temperature, item.unit, item.description, item.served_from_cache, item.timestamp.isoformat()])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=weather_history.csv"}
    )

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    # Проверка БД
    try:
        await db.execute(select(1))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # Проверка доступности API (с коротким таймаутом)
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://api.openweathermap.org", timeout=1.5)
            api_status = "reachable" if res.status_code < 500 else "unreachable"
    except Exception:
        api_status = "unreachable"

    if db_status != "healthy" or api_status != "reachable":
        raise HTTPException(status_code=503, detail={"database": db_status, "external_api": api_status})

    return {"status": "OK", "database": db_status, "external_api": api_status}
@app.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request,
    filter_city: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    # Получаем отфильтрованную историю для таблицы
    stmt = build_history_query(filter_city, date_from, date_to).limit(10)
    history_items = (await db.execute(stmt)).scalars().all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "history": history_items,
        "filter_city": filter_city,
        "current_weather": None
    })

@app.get("/web/weather", response_class=HTMLResponse)
async def web_weather(request: Request, city: str, unit: str = "C", db: AsyncSession = Depends(get_db)):
    current_weather = None
    try:
        current_weather = await fetch_weather_data(city, unit, db)
    except Exception as e:
        # Если произошла ошибка (например, города нет), можно прокинуть её описание в UI
        pass

    # Подгружаем историю для нижней таблицы, чтобы она не исчезала при поиске
    stmt = select(WeatherQuery).order_by(desc(WeatherQuery.timestamp)).limit(10)
    history_items = (await db.execute(stmt)).scalars().all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "history": history_items,
        "current_weather": current_weather
    })