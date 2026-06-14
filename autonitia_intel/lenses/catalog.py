"""
Signal catalog — loaded from declarative YAML packs, not hardcoded.

Layout (autonitia_intel/signal_packs/):
    lenses/automation.yaml, marketing.yaml, sales.yaml, ...
    industries/real_estate.yaml, ...

Each signal is declarative:

    - signal_id: no_online_booking
      lenses: [automation]
      title: No online booking detected
      severity: medium
      requires: { has_online_booking: false }     # AND over the fact namespace
      patterns: [calendly, "book a viewing", ...]  # cheap first-pass hints (broad)
      requirements: [online_scheduling, appointment_followup]  # problems it implies a need for
      industries: [real_estate]                    # optional: only fires for this industry

Adding a lens or a signal = adding YAML. No Python edits. `LENSES` is derived
from the packs, so a new lens pack introduces a new lens automatically.

The fact namespace for `requires` is a flat merge of Capabilities + SEO +
Tracking booleans, so a declarative `requires` can express every old lambda
(including the pixel/SEO special cases) without code.
"""

from pathlib import Path

import yaml

from ..models import Capabilities

_PACK_DIR = Path(__file__).parent.parent / "signal_packs"

# Industry display-name → pack slug
_INDUSTRY_ALIASES = {
    "real estate": "real_estate", "realestate": "real_estate", "property": "real_estate",
    "healthcare": "healthcare", "dental": "healthcare", "clinic": "healthcare", "medical": "healthcare",
    "automotive": "automotive_services", "car wash": "automotive_services", "detailing": "automotive_services",
    "ecommerce": "ecommerce", "e-commerce": "ecommerce", "online store": "ecommerce",
    "hospitality": "hospitality", "restaurant": "hospitality", "hotel": "hospitality",
}


def normalize_industry(industry: str | None) -> str | None:
    if not industry:
        return None
    key = industry.strip().lower()
    if key in _INDUSTRY_ALIASES:
        return _INDUSTRY_ALIASES[key]
    for alias, slug in _INDUSTRY_ALIASES.items():
        if alias in key:
            return slug
    return key.replace(" ", "_")


def _load_packs() -> dict:
    catalog: dict[str, dict] = {}
    if not _PACK_DIR.exists():
        return catalog
    for path in sorted(_PACK_DIR.rglob("*.yaml")):
        data = yaml.safe_load(path.read_text()) or {}
        for spec in data.get("signals", []):
            sid = spec["signal_id"]
            spec.setdefault("lenses", [])
            spec.setdefault("requires", {})
            spec.setdefault("patterns", [])
            spec.setdefault("requirements", [])
            spec.setdefault("severity", "medium")
            spec.setdefault("industries", [])
            spec.setdefault("impact", "")
            catalog[sid] = spec
    return catalog


SIGNAL_CATALOG: dict[str, dict] = _load_packs()

# Lenses are whatever the packs declare — not a fixed list.
LENSES: list[str] = sorted({lens for spec in SIGNAL_CATALOG.values() for lens in spec["lenses"]})


def _facts(caps: Capabilities, seo, tracking) -> dict:
    """Flat fact namespace for declarative `requires` checks."""
    facts = dict(caps.model_dump())
    if seo is not None:
        facts.update(seo.model_dump())
    if tracking is not None:
        facts.update(tracking.model_dump())
    return facts


def candidate_signals(caps: Capabilities, lens: str, industry: str | None = None,
                      seo=None, tracking=None) -> list[str]:
    """
    Return signal_ids that fire for this lens (+ optional industry).

    A signal fires when ALL of its `requires` facts match. Industry-tagged
    signals only fire when the (normalized) industry matches.
    """
    facts = _facts(caps, seo, tracking)
    industry_slug = normalize_industry(industry)
    out = []
    for sid, spec in SIGNAL_CATALOG.items():
        if lens not in spec["lenses"]:
            continue
        if spec["industries"] and industry_slug not in spec["industries"]:
            continue
        if all(facts.get(k) == v for k, v in spec["requires"].items()):
            out.append(sid)
    return out
