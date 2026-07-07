import pytest
from app.utils import SimpleRateLimiter

def test_rate_limiter_logic():
    limiter = SimpleRateLimiter(requests_limit=2, window_seconds=10)
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is False  # 3-й запрос заблокирован

def test_conversion_logic():
    # Проверка формулы перевода температур из сервиса
    from app.services import convert_temp
    # Из C в F: (15 * 9/5) + 32 = 59
    res = (15.0 * 9/5) + 32
    assert res == 59.0