"""AgentPulse Python SDK for trace and span instrumentation."""

import functools
import logging
import queue
import threading
import time
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, ParamSpec, TypeVar

import httpx

logger = logging.getLogger("agentpulse.sdk")

P = ParamSpec("P")
R = TypeVar("R")

# Thread-local storage for active trace and span hierarchy
_context_local = threading.local()


def _get_active_trace() -> "TraceContext | None":
    return getattr(_context_local, "active_trace", None)


def _get_active_span_id() -> uuid.UUID | None:
    return getattr(_context_local, "active_span_id", None)


def _set_active_span_id(span_id: uuid.UUID | None) -> None:
    _context_local.active_span_id = span_id


class SpanContext:
    """Represents an active span within a trace."""

    def __init__(
        self,
        name: str,
        kind: str = "agent",
        model: str | None = None,
        provider: str | None = None,
        parent_span_id: uuid.UUID | None = None,
    ) -> None:
        self.id = uuid.uuid4()
        self.parent_span_id = parent_span_id
        self.name = name
        self.kind = kind
        self.model = model
        self.provider = provider
        self.started_at = datetime.now(UTC)
        self.duration_ms = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.input: Any = None
        self.output: Any = None
        self.attributes: dict[str, Any] = {}
        self._start_perf = time.perf_counter()

    def record_usage(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """Record token counts for this span."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def end(self, output: Any = None) -> None:
        """Mark span as finished and calculate duration."""
        if output is not None:
            self.output = output
        self.duration_ms = max(1, int((time.perf_counter() - self._start_perf) * 1000))

    def to_dict(self) -> dict[str, Any]:
        """Serialize span for ingestion."""
        return {
            "id": str(self.id),
            "parent_span_id": str(self.parent_span_id) if self.parent_span_id else None,
            "kind": self.kind,
            "name": self.name,
            "started_at": self.started_at.isoformat(),
            "duration_ms": self.duration_ms,
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "input": self.input,
            "output": self.output,
            "attributes": self.attributes,
        }


class TraceContext:
    """Represents an active trace containing multiple spans."""

    def __init__(self, name: str, session_id: str | None = None) -> None:
        self.id = uuid.uuid4()
        self.name = name
        self.session_id = session_id
        self.started_at = datetime.now(UTC)
        self.status = "ok"
        self.spans: list[SpanContext] = []
        self._start_perf = time.perf_counter()

    def add_span(self, span: SpanContext) -> None:
        self.spans.append(span)

    def to_dict(self) -> dict[str, Any]:
        duration_ms = max(1, int((time.perf_counter() - self._start_perf) * 1000))
        total_in = sum(s.input_tokens for s in self.spans)
        total_out = sum(s.output_tokens for s in self.spans)

        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "duration_ms": duration_ms,
            "status": self.status,
            "input_tokens": total_in,
            "output_tokens": total_out,
            "spans": [s.to_dict() for s in self.spans],
        }


class AgentPulse:
    """Client for tracing and exporting traces to AgentPulse API."""

    def __init__(
        self,
        api_key: str = "ap_qa_devkey12345",
        base_url: str = "http://localhost:8000",
        flush_interval: float = 2.0,
        batch_size: int = 10,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        self._queue: queue.Queue[dict[str, Any] | None] = queue.Queue(maxsize=1000)
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def _worker_loop(self) -> None:
        buffer: list[dict[str, Any]] = []
        last_flush = time.time()

        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=0.5)
                if item is None:
                    break
                buffer.append(item)
            except queue.Empty:
                pass

            if buffer and (
                len(buffer) >= self.batch_size or (time.time() - last_flush) >= self.flush_interval
            ):
                self.send_batch(buffer)
                buffer = []
                last_flush = time.time()

        if buffer:
            self.send_batch(buffer)

    def send_batch(self, traces: list[dict[str, Any]]) -> None:
        url = f"{self.base_url}/v1/traces"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json={"traces": traces}, headers=headers)
                if res.status_code not in (200, 202):
                    logger.warning(
                        "Failed to export traces: status %s %s", res.status_code, res.text
                    )
        except Exception as exc:
            logger.warning("Error exporting traces to %s: %s", url, exc)

    def enqueue_trace(self, trace_data: dict[str, Any]) -> None:
        """Enqueue trace for asynchronous batch export."""
        try:
            self._queue.put_nowait(trace_data)
        except queue.Full:
            logger.warning("AgentPulse export queue is full. Dropping trace.")

    def flush(self) -> None:
        """Wait for pending traces to be transmitted."""
        # Drain queue
        while not self._queue.empty():
            time.sleep(0.1)

    def shutdown(self) -> None:
        """Stop worker thread and flush pending traces."""
        self._stop_event.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        self._worker_thread.join(timeout=3.0)

    @contextmanager
    def trace(self, name: str, session_id: str | None = None) -> Any:
        """Context manager for tracing an entire interaction."""
        trace = TraceContext(name=name, session_id=session_id)
        prev_trace = getattr(_context_local, "active_trace", None)
        _context_local.active_trace = trace
        try:
            yield trace
        except Exception:
            trace.status = "error"
            raise
        finally:
            _context_local.active_trace = prev_trace
            self.enqueue_trace(trace.to_dict())

    @contextmanager
    def span(
        self,
        name: str,
        kind: str = "agent",
        model: str | None = None,
        provider: str | None = None,
        input_data: Any = None,
    ) -> Any:
        """Context manager for recording an individual span."""
        trace = _get_active_trace()
        parent_id = _get_active_span_id()
        span = SpanContext(
            name=name,
            kind=kind,
            model=model,
            provider=provider,
            parent_span_id=parent_id,
        )
        if input_data is not None:
            span.input = input_data

        if trace is not None:
            trace.add_span(span)

        prev_span_id = parent_id
        _set_active_span_id(span.id)
        try:
            yield span
        finally:
            span.end()
            _set_active_span_id(prev_span_id)


# Global singleton instance
_default_client: AgentPulse | None = None


def get_client() -> AgentPulse:
    """Return default initialized AgentPulse client."""
    global _default_client
    if _default_client is None:
        _default_client = AgentPulse()
    return _default_client


def trace(
    name: str | None = None, session_id: str | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to trace a function execution."""

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        span_name = name or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            client = get_client()
            with client.trace(name=span_name, session_id=session_id):
                return fn(*args, **kwargs)

        return wrapper

    return decorator


def span(
    name: str | None = None,
    kind: str = "agent",
    model: str | None = None,
    provider: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to record a span inside an active trace."""

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        span_name = name or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            client = get_client()
            with client.span(name=span_name, kind=kind, model=model, provider=provider) as s:
                result = fn(*args, **kwargs)
                s.output = result
                return result

        return wrapper

    return decorator
