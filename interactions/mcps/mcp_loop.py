import asyncio
import threading

_loop = asyncio.new_event_loop()
_thread = threading.Thread(target=_loop.run_forever, daemon=True)
_thread.start()


def run_async(coro):
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result()
