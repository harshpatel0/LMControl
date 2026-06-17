"""
api/log_stream.py

Bridges sync logging calls and stdout writes into an asyncio.Queue
so the FastAPI WebSocket handler can stream them to the client.

Usage
-----
stream = LogStream()
stream.attach()        # install log handler + stdout redirect
...run orchestrator...
stream.detach()        # restore originals
"""

import asyncio
import logging
import sys
import io
import json
from datetime import datetime

# ── Sentinel: signals the queue is finished ──────────────────────────────────
_DONE = object()


class LogStream:
    """
    Collects log records and stdout writes and puts them onto an
    asyncio.Queue as JSON-serialisable dicts.

    Must be created on the event-loop thread, but attach()/detach()
    are safe to call from either thread.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.queue: asyncio.Queue = asyncio.Queue()
        self._handler = _QueueLogHandler(self)

        # 1. Define this line first:
        self._original_stdout = sys.stdout

        # 2. Then initialize the proxy:
        self._stdout_proxy = _StdoutProxy(self)

    def attach(self):
        """Install the log handler and stdout proxy."""
        root = logging.getLogger()
        root.addHandler(self._handler)

        lm = logging.getLogger("kodo")
        lm.addHandler(self._handler)

        sys.stdout = self._stdout_proxy

    def detach(self):
        """Restore originals and push the done sentinel."""
        sys.stdout = self._original_stdout

        root = logging.getLogger()
        root.removeHandler(self._handler)

        lm = logging.getLogger("kodo")
        lm.removeHandler(self._handler)

        self._put_threadsafe(_DONE)

    def put(self, record: dict):
        """Called from the sync thread; thread-safe queue push."""
        self._put_threadsafe(record)

    async def stream(self):
        """
        Async generator — yields dicts until the sentinel is received.
        Intended for consumption by the WebSocket handler.
        """
        while True:
            item = await self.queue.get()
            if item is _DONE:
                return
            yield item

    # ── Internal ──────────────────────────────────────────────────────────────

    def _put_threadsafe(self, item):
        self.loop.call_soon_threadsafe(self.queue.put_nowait, item)


class _QueueLogHandler(logging.Handler):
    """Logging handler that forwards records to a LogStream."""

    def __init__(self, stream: LogStream):
        super().__init__(level=logging.DEBUG)
        self._stream = stream
        self.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
                datefmt="%d-%m-%Y %H:%M:%S",
            )
        )

    def emit(self, record: logging.LogRecord):
        try:
            self._stream.put(
                {
                    "type": "log",
                    "level": record.levelname,
                    "module": record.module,
                    "message": self.format(record),
                    "ts": datetime.utcnow().isoformat(),
                }
            )
        except Exception:
            self.handleError(record)


class _StdoutProxy(io.TextIOBase):
    """
    Minimal stdout replacement that forwards writes to the LogStream
    *and* to the original stdout so the console still works.
    """

    def __init__(self, stream: LogStream):
        self._stream = stream
        self._original = stream._original_stdout
        self._buf = ""

    def write(self, text: str) -> int:
        # Mirror to real stdout
        self._original.write(text)
        self._original.flush()

        # Buffer until newline so we emit whole lines
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.strip()
            if line:
                self._stream.put(
                    {
                        "type": "stdout",
                        "level": "INFO",
                        "message": line,
                        "ts": datetime.utcnow().isoformat(),
                    }
                )
        return len(text)

    def flush(self):
        self._original.flush()

    # Required so logging's StreamHandler doesn't complain
    @property
    def encoding(self):
        return self._original.encoding

    @property
    def errors(self):
        return getattr(self._original, "errors", "strict")
