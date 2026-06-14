import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

CACHE_DIR = Path(__file__).parent.parent / "output" / ".cache"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
REQUEST_TIMEOUT = 15
MAX_CONTENT_CHARS = 24_000   # overall budget sent to the LLM
PER_PAGE_CHARS = 6_000       # per-page cap so no single page (e.g. a bloated homepage) starves the rest
MAX_SUBPAGES = 3

# Crawling politeness/resilience
RESPECT_ROBOTS = os.getenv("AUTONITIA_RESPECT_ROBOTS", "true").lower() != "false"
FETCH_RETRIES = int(os.getenv("AUTONITIA_FETCH_RETRIES", "2"))   # extra attempts on transient errors
ROBOTS_UA = "autonitia-intel"

# Telemetry — see telemetry/telemetry.py. Nothing is sent over the network in v0.1.
# Level 1 (execution metrics) is opt-OUT. Level 2 (dataset capture) is opt-IN.
TELEMETRY_ENABLED = os.getenv("AUTONITIA_TELEMETRY", "true").lower() != "false"
DATASET_CONTRIBUTION = os.getenv("AUTONITIA_DATASET", "false").lower() == "true"
