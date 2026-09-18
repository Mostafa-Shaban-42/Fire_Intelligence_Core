from alerts.rate_limiter import RateLimiter

def test_rate_limiter():
    limiter = RateLimiter(min_interval_sec=5.0)
    assert limiter.is_allowed("k1") is True
    assert limiter.is_allowed("k1") is False