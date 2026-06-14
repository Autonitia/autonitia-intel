"""Unit tests for deterministic detection — no network, no LLM."""

from autonitia_intel.detection import detect_capabilities, detect_tools, extract_contacts


def test_detect_tools_fingerprints():
    html = """
    <script src="https://cdn.shopify.com/s/files/x.js"></script>
    <script>fbq('init','123');</script>
    <script src="https://www.googletagmanager.com/gtm.js"></script>
    """
    names = {t["name"] for t in detect_tools(html)}
    assert "Shopify" in names
    assert "Meta Pixel" in names
    assert "Google Tag Manager" in names


def test_detect_tools_empty_on_plain_html():
    assert detect_tools("<html><body><h1>Hello</h1></body></html>") == []


def test_strong_booking_signal():
    html = '<a href="https://calendly.com/acme/intro">Book</a>'
    caps, *_rest, strong = detect_capabilities(html)
    assert caps.has_online_booking is True
    assert "has_online_booking" in strong  # tool URL → strong


def test_weak_booking_signal_not_strong():
    html = "<a href='/book-a-viewing'>Book a viewing</a>"
    caps, *_rest, strong = detect_capabilities(html)
    assert caps.has_online_booking is True          # weak text still detected
    assert "has_online_booking" not in strong       # but not strong → downgradable


def test_strong_whatsapp_url():
    caps, *_rest, strong = detect_capabilities('<a href="https://wa.me/971500000000">Chat</a>')
    assert caps.has_whatsapp is True
    assert "has_whatsapp" in strong


def test_weak_whatsapp_button():
    caps, *_rest, strong = detect_capabilities('<button aria-label="WhatsApp Us">x</button>')
    assert caps.has_whatsapp is True
    assert "has_whatsapp" not in strong


def test_strong_live_chat_tool():
    caps, *_rest, strong = detect_capabilities('<script src="https://widget.intercom.io/x"></script>')
    assert caps.has_live_chat is True
    assert "has_live_chat" in strong


def test_social_links_extracted():
    html = """
    <a href="https://www.facebook.com/acme">fb</a>
    <a href="https://ae.linkedin.com/company/acme">li</a>
    <a href="https://twitter.com/acme">x</a>
    """
    _caps, social, *_rest = detect_capabilities(html)
    assert social.facebook.endswith("/acme")
    assert "linkedin.com/company/acme" in social.linkedin
    assert social.x.endswith("/acme")


def test_social_share_links_ignored():
    html = '<a href="https://www.facebook.com/sharer/sharer.php?u=x">share</a>'
    _caps, social, *_rest = detect_capabilities(html)
    assert social.facebook == ""


def test_extract_contacts_email_phone_whatsapp():
    html = """
    <a href="mailto:hello@acme.com">email</a>
    <a href="tel:+971 4 892 5831">call</a>
    <a href="https://wa.me/971500000000">whatsapp</a>
    """
    c = extract_contacts(html)
    assert "hello@acme.com" in c["emails"]
    assert any("892 5831" in p for p in c["phones"])
    assert "wa.me/971500000000" in c["whatsapp"]


def test_extract_contacts_ignores_image_emails():
    html = '<img src="logo@2x.png">'
    c = extract_contacts(html)
    assert c["emails"] == []
