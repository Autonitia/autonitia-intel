"""
RepairExtractionNode — second extraction pass when the first found nothing.

Reached only via a conditional edge: if FactExtraction returns no company_name
(thin/awkward content, a transient blip, an unusual layout), we retry once with
a more forceful prompt before giving up. This is the "repair" step in
extract → validate → repair → verify → score. Guarded by state['repaired'] so
it can never loop.
"""

from openai import OpenAI

from ..config import MODEL, OPENAI_API_KEY
from ..graph.base_node import BaseNode
from ..models import FactExtraction
from ..usage import record_usage

SYSTEM = """You are re-reading a website because a first extraction pass found no
company name. Look harder and infer where reasonable:
- the company name may be in the page title, header, logo alt text, footer,
  copyright line, or the domain itself
- still extract industry, business_model, services, description, city, country,
  emails, phones, addresses where present
Only state facts supported by the content. Do not fabricate."""


class RepairExtractionNode(BaseNode):
    def execute(self, state: dict) -> dict:
        model = state.get("model") or MODEL
        client = OpenAI(api_key=state.get("api_key") or OPENAI_API_KEY)
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": (
                    f"Domain: {state.get('target_url','')}\n\n"
                    f"Website content:\n\n{state['combined_markdown']}"
                )},
            ],
            temperature=0,
            response_format=FactExtraction,
        )
        record_usage(state, "RepairExtractionNode", model, completion)
        repaired = completion.choices[0].message.parsed or FactExtraction()
        # Keep whichever pass found more (prefer repaired if it now has a name)
        if repaired.company_name or not state["facts"].company_name:
            state["facts"] = repaired
        state["repaired"] = True
        if state.get("verbose", True):
            print(f"      ↳ repair pass: company_name={state['facts'].company_name or '(still empty)'}")
        return state
