import json
import logging
import time
from datetime import UTC, datetime
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "x-request-id"
REQUEST_LOGGER_NAME = "ai_lab_portal.request"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach a request id and emit one sanitized JSON access log per request."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        response.headers[REQUEST_ID_HEADER] = request_id

        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "INFO",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "duration_ms": duration_ms,
            "status_code": response.status_code,
            "action": "http_request",
            "message": f"{request.method} {request.url.path} completed with {response.status_code}",
        }
        logging.getLogger(REQUEST_LOGGER_NAME).info(json.dumps(payload, separators=(",", ":")))
        return response
