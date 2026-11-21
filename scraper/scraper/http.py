from __future__ import annotations

import logging
import time
from collections import defaultdict
from urllib.parse import urlparse

import httpx

log = logging.getLogger(__name__)

# Treat these as blocked and do not retry; parser should surface them as failed.
_BLOCKED_STATUSES = frozenset({401, 403, 429})
_RETRY_STATUSES = frozenset({500, 502, 503, 504})


class RateLimiter:
    """Per-host token bucket: at most `rps` requests per second per host.

    Default 0.5 rps = 1 request / 2 s, matching our ethics rules
    (07 Provoz/Právní a etické zásady.md).
    """

    def __init__(self, rps: float = 0.5) -> None:
        self._interval = 1.0 / rps if rps > 0 else 0.0
        self._last_at: dict[str, float] = defaultdict(float)

    def wait(self, url: str) -> None:
        if self._interval <= 0:
            return
        host = urlparse(url).netloc
        now = time.monotonic()
        wait_s = self._last_at[host] + self._interval - now
        if wait_s > 0:
            time.sleep(wait_s)
        self._last_at[host] = time.monotonic()


class HttpClient:
    """Rate-limited HTTP client with simple retry for 5xx/timeouts.

    Does NOT retry on 401/403/429 — those indicate anti-bot or auth gates and
    retrying would only escalate. Scraper marks the run as failed instead.
    """

    def __init__(
        self,
        user_agent: str,
        rate_limit_rps: float = 0.5,
        timeout_s: float = 20.0,
        max_retries: int = 3,
    ) -> None:
        self._client = httpx.Client(
            headers={"User-Agent": user_agent, "Accept-Language": "cs,en;q=0.5"},
            timeout=timeout_s,
            follow_redirects=True,
        )
        self._limiter = RateLimiter(rate_limit_rps)
        self._max_retries = max_retries

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *exc) -> None:
        self._client.close()

    def get(self, url: str, **kwargs) -> httpx.Response:
        self._limiter.wait(url)
        return self._request("GET", url, **kwargs)

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = self._client.request(method, url, **kwargs)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exc = exc
                self._backoff_sleep(attempt)
                continue

            if resp.status_code in _BLOCKED_STATUSES:
                raise BlockedError(f"{resp.status_code} on {url}")
            if resp.status_code in _RETRY_STATUSES and attempt < self._max_retries:
                self._backoff_sleep(attempt)
                continue
            resp.raise_for_status()
            return resp

        assert last_exc is not None
        raise last_exc

    @staticmethod
    def _backoff_sleep(attempt: int) -> None:
        time.sleep(min(2 ** attempt, 10))


class BlockedError(RuntimeError):
    """Source returned 401/403/429 — treat as failed, do not retry."""
