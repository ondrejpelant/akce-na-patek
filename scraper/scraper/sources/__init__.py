from __future__ import annotations

from scraper.sources.base import Source

# Registry of enabled sources. Add a line per store once its parser is implemented.
REGISTRY: dict[str, type[Source]] = {}


def register(cls: type[Source]) -> type[Source]:
    REGISTRY[cls.code] = cls
    return cls


__all__ = ["REGISTRY", "Source", "register"]
