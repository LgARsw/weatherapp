import time
import json
import logging
from collections import defaultdict
from fastapi import Request, HTTPException, status

# Структурированный логгер (вывод key=value / JSON)
logger = logging.getLogger("weather_app")
handler = logging.StreamHandler()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def log_event(event_name: str, **kwargs):
    payload = {"event": event_name, "timestamp": time.time()}
    payload.update(kwargs)
    logger.info(json.dumps(payload))

# Простой инмемори рейт-лимитер по IP
class SimpleRateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int = 60):
        self.limit = requests_limit
        self.window = window_seconds
        self.history = defaultdict(list)

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        # Очистка старых логов
        self.history[ip] = [t for t in self.history[ip] if now - t < self.window]
        if len(self.history[ip]) >= self.limit:
            return False
        self.history[ip].append(now)
        return True

rate_limiter = SimpleRateLimiter(requests_limit=30)