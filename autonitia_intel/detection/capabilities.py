"""
Deterministic capability + digital-presence detection.

Inspects raw HTML across all fetched pages to determine observable facts:
lead-capture methods, social links, SEO basics, tracking. No LLM.

These are FACTS (present/absent), which become the evidence base for signals.
"""

import re

from ..detection.fingerprints import detect_tools
from ..models import Capabilities, SEO, SocialMedia, Tracking

SOCIAL_PATTERNS = {
    "facebook": r"https?://(?:www\.)?facebook\.com/[A-Za-z0-9_.\-/]+",
    "instagram": r"https?://(?:www\.)?instagram\.com/[A-Za-z0-9_.\-/]+",
    "linkedin": r"https?://(?:[a-z]{2}\.)?linkedin\.com/(?:company|in)/[A-Za-z0-9_.\-/]+",
    "tiktok": r"https?://(?:www\.)?tiktok\.com/@[A-Za-z0-9_.\-/]+",
    "youtube": r"https?://(?:www\.)?youtube\.com/[A-Za-z0-9_.\-/@]+",
    "x": r"https?://(?:www\.)?(?:twitter|x)\.com/[A-Za-z0-9_]+",
}

# STRONG patterns = a real third-party tool / explicit URL → trustworthy, the
# LLM verifier may NOT downgrade these. WEAK patterns = generic text heuristics
# ("book now") that are easily wrong → the LLM verifier MAY override them.
BOOKING_STRONG = [r"calendly\.com", r"fresha\.com", r"acuityscheduling\.com", r"booksy\.com",
                  r"simplybook\.(me|it)", r"setmore\.com", r"squareup\.com/appointments"]
BOOKING_WEAK = [r"book\s*now", r"book\s*online", r"schedule\s*(an?\s*)?appointment", r"book\s*a\s*viewing"]

LIVE_CHAT_STRONG = [r"intercom", r"driftt?\.com", r"tidio", r"tawk\.to", r"crisp\.chat", r"hs-scripts"]
LIVE_CHAT_WEAK = [r"livechat", r"chat\s*with\s*us", r"live\s*chat"]

WHATSAPP_STRONG = [r"wa\.me/", r"api\.whatsapp\.com", r"whatsapp://", r"web\.whatsapp\.com",
                   r"chat\.whatsapp\.com", r"wa\.link/"]
WHATSAPP_WEAK = [r"click\s*to\s*whatsapp", r'aria-label=["\'][^"\']*whatsapp', r"whatsapp\s*us"]

NEWSLETTER_STRONG = [r"chimpstatic", r"klaviyo", r"list-manage\.com"]
NEWSLETTER_WEAK = [r"newsletter", r"subscribe"]

# These have no reliable "strong" structural signal — treat as weak (downgradable).
PRICING_WEAK = [r"/pricing", r">\s*pricing\s*<", r">\s*plans\s*<", r"per\s*month", r"/mo\b"]
CASE_STUDY_WEAK = [r"case\s*stud", r"success\s*stor", r"/portfolio", r"testimonial"]
FORM_WEAK = [r"<form[\s>]"]  # a <form> could be search/login, not a contact form → downgradable

PHONE_PATTERN = r"tel:\+?[\d\s\-()]{7,}"
EMAIL_PATTERN = r"mailto:[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+"

# Capabilities the LLM verifier is allowed to downgrade when only a WEAK signal fired.
DOWNGRADABLE = {"has_online_booking", "has_whatsapp", "has_live_chat",
                "has_pricing", "has_case_studies", "has_contact_form", "has_newsletter"}


def _any(patterns: list[str], html: str) -> bool:
    return any(re.search(p, html, re.IGNORECASE) for p in patterns)


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_TEL_RE = re.compile(r'tel:(\+?[\d\s\-()]{7,})', re.IGNORECASE)
_WA_RE = re.compile(r'(https?://(?:wa\.me|wa\.link|api\.whatsapp\.com|web\.whatsapp\.com|chat\.whatsapp\.com)/[^\s"\'<>]+)', re.IGNORECASE)


def extract_contacts(html: str) -> dict:
    """Deterministic contact extraction — a backstop/merge for the LLM output."""
    emails = sorted({m.group(0) for m in _EMAIL_RE.finditer(html)
                     if not m.group(0).lower().endswith((".png", ".jpg", ".gif", ".webp", ".svg"))})
    phones = sorted({re.sub(r"\s+", " ", m.group(1)).strip() for m in _TEL_RE.finditer(html)})
    wa = ""
    m = _WA_RE.search(html)
    if m:
        wa = m.group(1)
    return {"emails": emails, "phones": phones, "whatsapp": wa}


def detect_capabilities(combined_html: str):
    """
    Returns (capabilities, social, seo, tracking, tools, strongly_detected).

    `strongly_detected` is the set of capability names backed by a STRONG
    structural signal (a real tool/URL). The LLM verifier may only downgrade
    capabilities NOT in this set.
    """
    booking_strong = _any(BOOKING_STRONG, combined_html)
    chat_strong = _any(LIVE_CHAT_STRONG, combined_html)
    wa_strong = _any(WHATSAPP_STRONG, combined_html)
    news_strong = _any(NEWSLETTER_STRONG, combined_html)

    caps = Capabilities(
        has_phone=bool(re.search(PHONE_PATTERN, combined_html, re.IGNORECASE)),
        has_email=bool(re.search(EMAIL_PATTERN, combined_html, re.IGNORECASE)),
        has_contact_form=_any(FORM_WEAK, combined_html),
        has_whatsapp=wa_strong or _any(WHATSAPP_WEAK, combined_html),
        has_online_booking=booking_strong or _any(BOOKING_WEAK, combined_html),
        has_live_chat=chat_strong or _any(LIVE_CHAT_WEAK, combined_html),
        has_pricing=_any(PRICING_WEAK, combined_html),
        has_case_studies=_any(CASE_STUDY_WEAK, combined_html),
        has_newsletter=news_strong or _any(NEWSLETTER_WEAK, combined_html),
    )

    strongly_detected = set()
    if booking_strong:
        strongly_detected.add("has_online_booking")
    if chat_strong:
        strongly_detected.add("has_live_chat")
    if wa_strong:
        strongly_detected.add("has_whatsapp")
    if news_strong:
        strongly_detected.add("has_newsletter")

    social = SocialMedia()
    for field, pattern in SOCIAL_PATTERNS.items():
        m = re.search(pattern, combined_html, re.IGNORECASE)
        if m:
            # Skip share/intent links — keep only profile-looking URLs
            url = m.group(0)
            if "sharer" not in url and "intent" not in url and "/share" not in url:
                setattr(social, field, url)
    caps.has_social_links = any(getattr(social, f) for f in SOCIAL_PATTERNS)

    seo = SEO(
        title_tag_present=bool(re.search(r"<title[\s>]", combined_html, re.IGNORECASE)),
        meta_description_present=bool(re.search(r'<meta[^>]+name=["\']description["\']', combined_html, re.IGNORECASE)),
    )

    tools = detect_tools(combined_html)
    tool_names = {t["name"] for t in tools}
    tracking = Tracking(
        google_analytics="Google Analytics" in tool_names,
        google_tag_manager="Google Tag Manager" in tool_names,
        meta_pixel="Meta Pixel" in tool_names,
        tiktok_pixel="TikTok Pixel" in tool_names,
        linkedin_pixel="LinkedIn Insight" in tool_names,
        hotjar="Hotjar" in tool_names,
    )

    return caps, social, seo, tracking, tools, strongly_detected
