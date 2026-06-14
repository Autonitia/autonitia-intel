"""
BasicAssembleNode — build the free ProfileResult (facts + presence + pro_features).

The pro_features COUNTS candidate opportunities deterministically (via the gap rules
in lenses/catalog.py) without revealing them — that's the upgrade hook to Pro.
No LLM, no scores, no signal detail here.
"""

from urllib.parse import urlparse

from ..graph.base_node import BaseNode
from ..lenses import candidate_signals
from ..models import Contact, DigitalPresence, ProfileResult, TargetCompany, ProFeatures


def _merge_unique(*lists) -> list[str]:
    seen, out = set(), []
    for lst in lists:
        for item in lst or []:
            key = item.strip().lower()
            if item.strip() and key not in seen:
                seen.add(key)
                out.append(item.strip())
    return out


class BasicAssembleNode(BaseNode):
    def execute(self, state: dict) -> dict:
        facts = state["facts"]
        caps = state["capabilities"]
        lens = state["lens"]
        location = ", ".join([p for p in [facts.city, facts.country] if p])

        det = state.get("contacts_detected", {})
        contact = Contact(
            emails=_merge_unique(facts.emails, det.get("emails", [])),
            phones=_merge_unique(facts.phones, det.get("phones", [])),
            whatsapp=det.get("whatsapp", ""),
            addresses=_merge_unique(facts.addresses),
        )

        present = [k.replace("has_", "") for k, v in caps.model_dump().items()
                   if k.startswith("has_") and v]

        # ProFeatures: deterministic gap COUNT for this lens + detected industry
        gaps = candidate_signals(caps, lens, industry=facts.industry,
                                 seo=state.get("seo"), tracking=state.get("tracking"))
        n = len(gaps)
        if n:
            msg = f"{n} potential opportunit{'y' if n == 1 else 'ies'} detected for the '{lens}' lens."
        else:
            msg = f"No obvious gaps detected for the '{lens}' lens."

        state["result"] = ProfileResult(
            target_company=TargetCompany(
                name=facts.company_name,
                domain=urlparse(state["target_url"]).netloc,
                industry=facts.industry,
                business_model=facts.business_model,
                description=facts.description,
                location=location,
                services=facts.services,
                contact=contact,
            ),
            digital_presence=DigitalPresence(
                social_media=state["social_media"],
                seo=state["seo"],
                tracking=state["tracking"],
            ),
            capabilities_present=present,
            detected_tools=state["detected_tools"],
            pro_features=ProFeatures(lens=lens, opportunities_found=n, message=msg),
        )
        # Keep candidate ids in state for the Pro layer to reuse (not in free output)
        state["candidate_signal_ids"] = gaps
        return state
