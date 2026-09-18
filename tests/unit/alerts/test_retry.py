import pytest
from alerts.retry import RetryHandler

@pytest.mark.asyncio
async def test_retry_success():
    handler = RetryHandler(max_retries=2, backoff_base=0.01)
    async def dummy(): return True
    assert await handler.execute(dummy) is True