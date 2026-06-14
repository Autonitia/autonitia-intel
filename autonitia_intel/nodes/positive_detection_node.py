"""
PositiveDetectionNode — deterministic detection of what's PRESENT (no LLM).

The free tier reports observable facts: present capabilities, tech/tracking
tools, social links, SEO basics, and contact details. It does NOT verify
absences or articulate gaps — that's the Pro layer's job.
"""

from ..detection import detect_capabilities, extract_contacts
from ..graph.base_node import BaseNode
from ..models import DetectedTool


class PositiveDetectionNode(BaseNode):
    def execute(self, state: dict) -> dict:
        caps, social, seo, tracking, tools, strongly_detected = detect_capabilities(state["combined_html"])
        state["capabilities"] = caps
        state["social_media"] = social
        state["seo"] = seo
        state["tracking"] = tracking
        state["detected_tools"] = [DetectedTool(**t) for t in tools]
        state["strongly_detected"] = strongly_detected
        state["contacts_detected"] = extract_contacts(state["combined_html"])
        return state
