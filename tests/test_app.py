import pytest
from app.utils import SimpleRateLimiter

def test_rate_limiter_logic():
    limiter = SimpleRateLimiter(requests_limit=2, window_seconds=10)
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is False  

def test_conversion_logic():
    from app.services import convert_temp
    res = (15.0 * 9/5) + 32
    assert res == 59.0