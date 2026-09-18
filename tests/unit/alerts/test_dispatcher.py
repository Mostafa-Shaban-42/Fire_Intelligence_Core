import pytest
from alerts.dispatcher import AlertDispatcher
from alerts.channels.telegram import TelegramAlertChannel

@pytest.mark.asyncio
async def test_dispatcher():
    disp = AlertDispatcher([TelegramAlertChannel()])
    # Assumes valid call
    assert disp is not None