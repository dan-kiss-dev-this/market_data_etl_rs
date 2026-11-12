import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

# Local Postgres.app by default; point it at another database (e.g. Supabase) to switch
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres@localhost:5432/market")

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
