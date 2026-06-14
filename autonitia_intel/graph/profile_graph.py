"""
ProfileGraph — the FREE (open-source) entry point.

Pipeline (with a repair branch):

  Fetch → Markdownify → FactExtraction ─┬─(no company found)→ RepairExtraction ─┐
                                        └─────────────────────────────────────→ PositiveDetection
  PositiveDetection → BasicAssemble → END

What it returns: a clean company profile (facts, contact, social, present
capabilities, detected tools) plus a *pro_features* count of opportunities. The
intelligence layer (verified signals, scores, offer matching, outreach) is the
Pro product, which reuses these same nodes via the exported building blocks.

Bring your own model key: pass `api_key`/`model` to ProfileGraph.
"""

from ..lenses import LENSES
from ..models import CompanyProfile, ProfileResult
from ..nodes import (
    BasicAssembleNode,
    FactExtractionNode,
    FetchNode,
    MarkdownifyNode,
    PositiveDetectionNode,
    RepairExtractionNode,
)
from ..telemetry import record
from ..usage import usage_totals
from .base_graph import END, BaseGraph


def _after_extraction(state: dict) -> str:
    """Repair branch: retry extraction once if the first pass found no company."""
    if not state["facts"].company_name and not state.get("repaired"):
        return "RepairExtractionNode"
    return "PositiveDetectionNode"


class ProfileGraph:
    """
    Open-source profile extractor.

    Two ways to construct it:

    1. Config-first (recommended for quick adoption):

        config = {
            "llm": {"model": "gpt-4o-mini", "api_key": "sk-..."},  # api_key optional (env works)
            "lens": "automation",
            "verbose": True,
            "cache": True,
        }
        graph = ProfileGraph(source="https://example.com", config=config)
        result = graph.run()

    2. Keyword args:

        graph = ProfileGraph(lens="automation")
        result = graph.run("https://example.com")
    """

    def __init__(
        self,
        provider: CompanyProfile | None = None,
        lens: str = "automation",
        telemetry: bool = True,
        verbose: bool = True,
        api_key: str | None = None,
        model: str | None = None,
        source: str | None = None,
        config: dict | None = None,
    ):
        config = config or {}
        llm = config.get("llm", {})
        # config values take precedence when provided
        lens = config.get("lens", lens)
        verbose = config.get("verbose", verbose)
        telemetry = config.get("telemetry", telemetry)
        api_key = llm.get("api_key", api_key)
        model = llm.get("model", model)

        if lens not in LENSES:
            raise ValueError(f"lens must be one of {LENSES}, got '{lens}'")
        # Provider is optional for the free profile tier (only the pro_features lens uses it indirectly).
        self.provider = provider or CompanyProfile(name="")
        self.lens = lens
        self.telemetry = telemetry
        self.verbose = verbose
        self.api_key = api_key
        self.model = model
        self.source = source
        self.use_cache = config.get("cache", True)
        self.graph = BaseGraph(
            nodes=[
                FetchNode(),
                MarkdownifyNode(),
                FactExtractionNode(),
                RepairExtractionNode(),     # reached only via the repair branch
                PositiveDetectionNode(),
                BasicAssembleNode(),
            ],
            edges={
                "FetchNode": "MarkdownifyNode",
                "MarkdownifyNode": "FactExtractionNode",
                "FactExtractionNode": _after_extraction,   # → Repair | PositiveDetection
                "RepairExtractionNode": "PositiveDetectionNode",
                "PositiveDetectionNode": "BasicAssembleNode",
                "BasicAssembleNode": END,
            },
            entry="FetchNode",
            verbose=verbose,
        )

    def run(self, target_url: str | None = None, target_industry_hint: str = "",
            use_cache: bool | None = None) -> ProfileResult:
        target_url = target_url or self.source
        if not target_url:
            raise ValueError("No URL given — pass run(url) or ProfileGraph(source=url).")
        if use_cache is None:
            use_cache = self.use_cache
        if not target_url.startswith("http"):
            target_url = "https://" + target_url

        state = {
            "target_url": target_url,
            "target_industry_hint": target_industry_hint,
            "use_cache": use_cache,
            "provider": self.provider,
            "lens": self.lens,
            "verbose": self.verbose,
            "api_key": self.api_key,
            "model": self.model,
        }
        state = self.graph.execute(state)
        result: ProfileResult = state["result"]

        if self.telemetry:
            record({
                "event_type": "profile_extraction",
                "target_domain": result.target_company.domain,
                "industry_detected": result.target_company.industry,
                "lens": self.lens,
                "opportunities_found": result.pro_features.opportunities_found,
                "usage": usage_totals(state),
                "execution": {"trace": state.get("_trace", []), "success": True},
            })
        return result
