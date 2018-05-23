import asyncio
from unittest import mock

async def async_print(msg):
    print(msg)

def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

def AsyncMock(*args, **kwargs):
    m = mock.MagicMock(*args, **kwargs)

    # make the coroutine return MagicMock obj
    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    # add the mock object to coroutine object to be used later
    mock_coro.mock = m
    return mock_coro