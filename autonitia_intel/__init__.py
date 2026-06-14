"""
autonitia-intel — open-source business-website profile extractor.

The FREE engine turns any business website into a clean structured profile
(company facts, contact details, social presence, detected tools/capabilities)
plus a *pro_features* count of opportunities. The intelligence layer — verified
signals, scoring, offer matching, outreach — is Autonitia Intel Pro, which
imports these same building blocks.

Quick start:

    from autonitia_intel import ProfileGraph

    graph = ProfileGraph(lens="automation")          # bring your own key via env or args
    profile = graph.run("https://example.com")
    print(profile.model_dump_json(indent=2))

Bring your own model key:

    ProfileGraph(api_key="sk-...", model="gpt-4o-mini")
"""

from .graph import ProfileGraph
from .models import CompanyProfile, ProfileResult

__version__ = "0.2.0"
__all__ = ["ProfileGraph", "CompanyProfile", "ProfileResult"]
