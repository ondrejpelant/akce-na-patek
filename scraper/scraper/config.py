from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRAPER_ROOT = Path(__file__).resolve().parents[1]

# Load scraper/.env (not committed). Keep connection strings and tokens out of the repo.
load_dotenv(SCRAPER_ROOT / ".env")


@dataclass(frozen=True)
class Config:
    database_url: str
    user_agent: str
    rate_limit_rps: float
    revalidate_url: str | None
    revalidate_token: str | None
    log_dir: Path

    @classmethod
    def from_env(cls) -> Config:
        database_url = os.environ.get("DATABASE_URL", "")
        if not database_url:
            raise RuntimeError(
                "DATABASE_URL není nastavená. Zkopíruj scraper/.env.example do scraper/.env "
                "a vyplň connection string z Neonu (role etl_rw)."
            )
        return cls(
            database_url=database_url,
            user_agent=os.environ.get(
                "USER_AGENT",
                "AkceNaPatek/0.1 (osobni nekomercni projekt)",
            ),
            rate_limit_rps=float(os.environ.get("RATE_LIMIT_RPS", "0.5")),
            revalidate_url=os.environ.get("REVALIDATE_URL") or None,
            revalidate_token=os.environ.get("REVALIDATE_TOKEN") or None,
            log_dir=SCRAPER_ROOT / "logs",
        )
