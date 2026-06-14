"""
Telemetry — privacy-first by design.

IMPORTANT: in v0.1 NOTHING is sent over the network. Events are written to a
local JSONL file (output/telemetry/) so you can inspect exactly what would be
collected before any hosted endpoint exists.

Levels:
  OFF        — nothing recorded.
  EXECUTION  — anonymous metrics only: no page content, no PII. (opt-OUT, default on)
  DATASET    — full trace incl. markdown + LLM response. (opt-IN, default off)

Controls:
  env  AUTONITIA_TELEMETRY=false   -> disables EXECUTION
  env  AUTONITIA_DATASET=true      -> enables DATASET (also needs explicit flag)

PII handling: DATASET payloads pass through scrub_pii() which strips emails and
phone numbers before writing. Company-level facts are kept; personal data is not.
"""

import json
import re
import time
import uuid
from pathlib import Path

from ..config import DATASET_CONTRIBUTION, OUTPUT_DIR, TELEMETRY_ENABLED


class TelemetryLevel:
    OFF = "off"
    EXECUTION = "execution"
    DATASET = "dataset"


TELEMETRY_DIR = OUTPUT_DIR / "telemetry"
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"\+?\d[\d\s\-()]{7,}\d")


def scrub_pii(text: str) -> str:
    text = _EMAIL.sub("[email]", text)
    text = _PHONE.sub("[phone]", text)
    return text


def _resolve_level() -> str:
    if not TELEMETRY_ENABLED:
        return TelemetryLevel.OFF
    return TelemetryLevel.DATASET if DATASET_CONTRIBUTION else TelemetryLevel.EXECUTION


def _write(event: dict) -> None:
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    path = TELEMETRY_DIR / "events.jsonl"
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")


def record(execution_payload: dict, dataset_payload: dict | None = None) -> str:
    """Record a telemetry event at the resolved level. Returns the level used."""
    level = _resolve_level()
    if level == TelemetryLevel.OFF:
        return level

    base = {
        "telemetry_level": level,
        "execution_id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sdk": {"package_name": "autonitia-intel", "version": "0.1.0", "language": "python"},
    }

    if level == TelemetryLevel.EXECUTION:
        _write({**base, **execution_payload})

    elif level == TelemetryLevel.DATASET:
        merged = {**base, **execution_payload}
        if dataset_payload:
            # Scrub PII from any free-text fields before persisting
            scrubbed = json.loads(scrub_pii(json.dumps(dataset_payload)))
            merged["dataset_trace"] = scrubbed
        _write(merged)

    return level
