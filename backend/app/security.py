"""Simple in-memory rate limiter and security headers middleware."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse


# ── In-memory rate limiter ──────────────────────────────────────


class RateLimiter:
    """Simple sliding-window rate limiter per IP.

    Not for production use (no persistence, no distributed sync).
    Sufficient for admin API protection against casual abuse.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = {}

    def check(self, ip: str) -> bool:
        """Check if a request from this IP is allowed.

        Returns True if allowed, False if rate-limited.
        """
        now = time.time()
        window_start = now - self.window_seconds

        if ip not in self._buckets:
            self._buckets[ip] = []

        # Prune old entries
        self._buckets[ip] = [
            t for t in self._buckets[ip] if t > window_start
        ]

        if len(self._buckets[ip]) >= self.max_requests:
            return False

        self._buckets[ip].append(now)
        return True


# ── Security headers middleware ─────────────────────────────────


def add_security_headers_middleware(app: FastAPI) -> None:
    """Add security headers to all responses."""

    @app.middleware("http")
    async def _add_security_headers(
        request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        return response


# ── Rate limiting middleware ────────────────────────────────────


def add_rate_limiting_middleware(
    app: FastAPI,
    max_requests: int = 120,
    window_seconds: int = 60,
) -> None:
    """Add rate limiting to all routes.

    Returns 429 Too Many Requests when the limit is exceeded.
    """
    limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)

    @app.middleware("http")
    async def _rate_limit(
        request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        # Only rate-limit admin routes
        if not request.url.path.startswith("/admin/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        if not limiter.check(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(window_seconds)},
            )

        return await call_next(request)
