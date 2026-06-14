"""
Deterministic technology detection.

A pragmatic subset of Wappalyzer-style fingerprints: each entry matches a
substring/regex in the raw HTML. NO LLM involved — this is fact, not inference,
which is why it's the most defensible signal in the product.

For production, swap this dict for the full Wappalyzer fingerprint database
(https://github.com/enthec/webappanalyzer) — same matching approach, ~3000 apps.
"""

import re

# name -> (category, [patterns], confidence)
FINGERPRINTS: dict[str, tuple[str, list[str], float]] = {
    # CMS / site builders
    "WordPress": ("cms", [r"wp-content", r"wp-includes"], 0.92),
    "Shopify": ("ecommerce", [r"cdn\.shopify\.com", r"Shopify\.theme"], 0.95),
    "Wix": ("cms", [r"static\.wixstatic\.com", r"_wixCssImports"], 0.9),
    "Webflow": ("cms", [r"assets\.website-files\.com", r"webflow\.js", r"wf-"], 0.88),
    "Squarespace": ("cms", [r"squarespace", r"static1\.squarespace\.com"], 0.9),
    "WooCommerce": ("ecommerce", [r"woocommerce", r"wc-ajax"], 0.85),
    # Analytics / tracking
    "Google Analytics": ("analytics", [r"google-analytics\.com", r"gtag\(", r"ga\('create'"], 0.9),
    "Google Tag Manager": ("analytics", [r"googletagmanager\.com"], 0.92),
    "Meta Pixel": ("marketing_tracking", [r"fbq\(", r"connect\.facebook\.net/[a-z_]+/fbevents\.js"], 0.93),
    "TikTok Pixel": ("marketing_tracking", [r"analytics\.tiktok\.com"], 0.9),
    "LinkedIn Insight": ("marketing_tracking", [r"snap\.licdn\.com"], 0.9),
    "Hotjar": ("analytics", [r"static\.hotjar\.com", r"hotjar"], 0.85),
    # CRM / marketing / chat
    "HubSpot": ("crm", [r"js\.hs-scripts\.com", r"hs-scripts"], 0.9),
    "Intercom": ("live_chat", [r"widget\.intercom\.io", r"intercomSettings"], 0.9),
    "Drift": ("live_chat", [r"js\.driftt\.com", r"drift\.com"], 0.88),
    "Tidio": ("live_chat", [r"code\.tidio\.co"], 0.9),
    "Tawk.to": ("live_chat", [r"embed\.tawk\.to"], 0.9),
    "Crisp": ("live_chat", [r"client\.crisp\.chat"], 0.9),
    "Mailchimp": ("email_marketing", [r"chimpstatic\.com", r"list-manage\.com"], 0.85),
    "Klaviyo": ("email_marketing", [r"klaviyo"], 0.85),
    # Booking / forms
    "Calendly": ("booking", [r"calendly\.com"], 0.92),
    "Fresha": ("booking", [r"fresha\.com"], 0.9),
    "Acuity Scheduling": ("booking", [r"acuityscheduling\.com"], 0.9),
    "Booksy": ("booking", [r"booksy\.com"], 0.9),
    "SimplyBook": ("booking", [r"simplybook\.(me|it)"], 0.88),
    "Typeform": ("forms", [r"typeform\.com"], 0.88),
    "Jotform": ("forms", [r"jotform\.com"], 0.88),
}


def detect_tools(html: str) -> list[dict]:
    """Return a list of detected tools: {name, category, confidence, evidence}."""
    found = []
    for name, (category, patterns, confidence) in FINGERPRINTS.items():
        for pat in patterns:
            if re.search(pat, html, re.IGNORECASE):
                found.append({
                    "name": name,
                    "category": category,
                    "confidence": confidence,
                    "evidence": f"matched /{pat}/",
                })
                break
    return found
