# autonitia-intel

Turn any business website into a clean, structured company profile — and a quick read on where the opportunities are.

Point it at a URL and get back the company's details (description, services, contact info, social presence) plus the tools and capabilities its site exposes. It also tells you how many opportunities a given **lens** (automation, marketing, sales…) would surface.

## Install

```bash
pip install autonitia-intel
playwright install chromium      # only needed for JavaScript-heavy sites
export OPENAI_API_KEY=sk-...      # or pass api_key in the config
```

## Use it

```python
from autonitia_intel import ProfileGraph

config = {
    "llm": {"model": "gpt-4o-mini"},   # add "api_key": "sk-..." or use the env var
    "lens": "automation",              # automation | marketing | sales | …
    "verbose": True,
}

graph = ProfileGraph(source="https://example.com", config=config)
result = graph.run()

print(result.model_dump_json(indent=2))
```

Prefer the command line?

```bash
python run.py https://example.com --lens marketing --json
```

## What you get

```json
{
  "target_company": {
    "name": "Example Co",
    "industry": "Real Estate",
    "description": "...",
    "location": "Dubai, UAE",
    "contact": { "phones": ["..."], "emails": ["..."], "addresses": ["..."] }
  },
  "digital_presence": { "social_media": { "linkedin": "...", "instagram": "..." } },
  "capabilities_present": ["phone", "whatsapp", "online_booking"],
  "pro_features": { "lens": "automation", "opportunities_found": 2 }
}
```

## How it works

It fetches the site politely (respecting `robots.txt`, with retries and a real-browser fallback for JS-heavy pages), uses one LLM call to read out the company profile, and runs fast local checks to spot the tools and capabilities present. The opportunity count for a lens is computed locally — no guessing.

## Lenses

A **lens** is the perspective you analyse a site through — `automation`, `marketing`, `sales`, and more. Lenses and the signals they look for are defined as simple **YAML packs** in [`autonitia_intel/signal_packs/`](autonitia_intel/signal_packs), so you can add a new lens or industry pack without touching the Python.

## Contributing

Contributions welcome — the easiest place to start is a signal pack: drop a YAML file under `signal_packs/lenses/` or `signal_packs/industries/` and open a PR. Run the tests with `pytest -m "not integration"`.

## Hosted version

This open-source engine gives you the profile and the opportunity count. The hosted **Autonitia Intel** turns those opportunities into verified, ranked, outreach-ready intelligence over a REST API.

**→ Docs & access: [autonitia.ai/intel](https://autonitia.ai/intel)**

| | Free — `autonitia-intel` | Hosted — Autonitia Intel |
|---|:---:|:---:|
| Company profile + contact + socials | ✅ | ✅ |
| Tool & capability detection | ✅ | ✅ |
| Opportunity count | ✅ | — |
| Verified capability analysis | — | ✅ |
| Pain signals with evidence | — | ✅ |
| Scoring (fit / opportunity / confidence) | — | ✅ |
| Offer matching + ranked opportunities | — | ✅ |
| Outreach messages | — | ✅ |
| External enrichment (founders, HQ, funding) | — | ✅ |
| REST API, async jobs, webhooks, CRM export | — | ✅ |

## License

MIT — see [LICENSE](LICENSE).
