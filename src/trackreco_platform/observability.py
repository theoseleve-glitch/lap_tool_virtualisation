import logging
import time
from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="n/a")
logger = logging.getLogger("trackreco.observability")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("x-correlation-id", str(uuid4()))
        token = correlation_id_ctx.set(correlation_id)
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["x-correlation-id"] = correlation_id
        logger.info(
            "request.complete",
            extra={
                "correlation_id": correlation_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "latency_ms": round(elapsed_ms, 2),
            },
        )
        correlation_id_ctx.reset(token)
        return response


def current_correlation_id() -> str:
    return correlation_id_ctx.get()
