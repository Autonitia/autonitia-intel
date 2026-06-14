"""FactExtractionNode — LLM extracts target company facts (structured output)."""

from openai import OpenAI

from ..config import MODEL, OPENAI_API_KEY
from ..graph.base_node import BaseNode
from ..models import FactExtraction
from ..usage import record_usage

SYSTEM = """You extract factual company information from website content
(homepage + contact/about/pricing sub-pages are included).

Extract:
- company_name, industry, business_model, services, description (one sentence)
- city, country
- emails: ALL contact email addresses found
- phones: ALL contact phone numbers found (include country code if shown)
- addresses: ALL physical office addresses (a company may list several offices)

Only include facts explicitly present. Use empty strings/lists for unknowns.
Do NOT guess or fabricate. business_model examples: 'Local service business',
'SaaS', 'E-commerce', 'Agency', 'Marketplace'."""


class FactExtractionNode(BaseNode):
    def execute(self, state: dict) -> dict:
        # Bring-your-own-key: state overrides env (free tier supplies its own).
        model = state.get("model") or MODEL
        client = OpenAI(api_key=state.get("api_key") or OPENAI_API_KEY)
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Website content:\n\n{state['combined_markdown']}"},
            ],
            temperature=0,
            response_format=FactExtraction,
        )
        record_usage(state, "FactExtractionNode", model, completion)
        state["facts"] = completion.choices[0].message.parsed or FactExtraction()
        return state
