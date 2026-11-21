from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from scraper.http import HttpClient
from scraper.models import ScrapedItem


class Source(ABC):
    """Abstract source. One subclass per store.

    Rules:
      - fetch() must be pure wrt. the DB. It only hits the network and yields items.
      - The CLI wraps fetch() with staging, sanity checks and error handling.
      - needs_browser=True triggers Playwright bootstrap in the CLI (not here).
    """

    code: str
    needs_browser: bool = False

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    @abstractmethod
    def fetch(self) -> Iterator[ScrapedItem]:
        """Yield one ScrapedItem per observed price."""
