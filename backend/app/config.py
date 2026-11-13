import os
from collections.abc import Mapping
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
# Doesn't override variables already set, so `uv run --env-file .env.production ...` wins
load_dotenv(BACKEND_DIR / ".env")


def database_url(environ: Mapping[str, str]) -> str:
    """Local Postgres.app (dev) when unset; .env.production points it at Supabase (production)."""
    url = environ.get("DATABASE_URL")
    if url is None:
        return "postgresql://postgres@localhost:5432/market"
    if not url.strip():
        # psycopg would read "" as the local Unix socket and fail with a misleading error
        raise RuntimeError(
            "DATABASE_URL is set but empty; in GitHub Actions this means the repo has no DATABASE_URL secret"
        )
    return url


DATABASE_URL = database_url(os.environ)

# Massive is the rebranded Polygon.io; api.polygon.io is the legacy host
MASSIVE_BASE_URL = "https://api.massive.com"
MASSIVE_API_KEY = os.environ.get("MASSIVE_API_KEY", "")

CONSTITUENTS_URL = (
    "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
)
BENCHMARK = "SPY"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
BLURB_MODEL = "claude-haiku-5-5"
# Leaders: the top companies by RS rating, the ones that get a Blurb
LEADER_COUNT = 50
# The AI Researcher panel stops showing a Blurb this many days after its rated date
BLURB_MAX_AGE_DAYS = 7

# ChatWithAI: follow-up questions about a Leader in the AI Researcher panel
CHAT_MODEL = "claude-haiku-5-5"
# Messages per visitor per UTC day, and across the whole site; the site cap bounds the daily cost
CHAT_VISITOR_DAILY = 5
CHAT_SITE_DAILY = 100
CHAT_MAX_CHARS = 250
CHAT_MAX_TOKENS = 1024
