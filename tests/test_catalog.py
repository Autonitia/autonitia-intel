"""Unit tests for the deterministic gap catalog (drives the free pro_features count)."""

from autonitia_intel.lenses import candidate_signals
from autonitia_intel.models import Capabilities


def test_candidate_signals_automation_gaps():
    caps = Capabilities(has_phone=True)  # everything else absent → many gaps
    ids = candidate_signals(caps, "automation")
    assert "no_online_booking" in ids
    assert "no_whatsapp_cta" in ids


def test_no_signal_when_capability_present():
    caps = Capabilities(has_online_booking=True, has_whatsapp=True, has_live_chat=True,
                        has_contact_form=True, has_phone=True)
    ids = candidate_signals(caps, "automation")
    assert "no_online_booking" not in ids
    assert "no_whatsapp_cta" not in ids


def test_lens_changes_candidates():
    caps = Capabilities(has_phone=True)
    auto = set(candidate_signals(caps, "automation"))
    mkt = set(candidate_signals(caps, "marketing"))
    assert auto != mkt  # different lenses surface different gaps


def test_pro_features_count_is_just_length():
    caps = Capabilities(has_phone=True)
    ids = candidate_signals(caps, "automation")
    assert isinstance(ids, list) and len(ids) >= 1


# ── Declarative packs / industry / requirements ────────────────

def test_lenses_are_derived_from_packs():
    from autonitia_intel.lenses import LENSES
    # Lenses introduced purely by the real_estate industry pack
    assert "lead_management" in LENSES
    assert "customer_reengagement" in LENSES


def test_industry_signal_only_fires_for_that_industry():
    caps = Capabilities(has_phone=True, has_contact_form=True)
    generic = candidate_signals(caps, "automation")
    re_specific = candidate_signals(caps, "automation", industry="Real Estate")
    assert "viewing_flow_manual_followup_risk" not in generic
    assert "viewing_flow_manual_followup_risk" in re_specific


def test_industry_normalization():
    from autonitia_intel.lenses.catalog import normalize_industry
    assert normalize_industry("Real Estate") == "real_estate"
    assert normalize_industry("dental clinic") == "healthcare"
    assert normalize_industry(None) is None


def test_signals_carry_requirements():
    from autonitia_intel.lenses import SIGNAL_CATALOG
    # signal → required problems/capabilities (not a vendor offer)
    assert SIGNAL_CATALOG["no_newsletter_capture"]["requirements"] == ["lead_capture", "lead_nurture"]
    assert "appointment_followup" in SIGNAL_CATALOG["no_online_booking"]["requirements"]


def test_declarative_requires_compound_condition():
    from autonitia_intel.models import SEO, Tracking
    # phone_only_cta needs phone present AND no booking AND no whatsapp
    caps = Capabilities(has_phone=True)
    assert "phone_only_cta" in candidate_signals(caps, "automation")
    caps2 = Capabilities(has_phone=True, has_whatsapp=True)
    assert "phone_only_cta" not in candidate_signals(caps2, "automation")
    # marketing pixel signal uses tracking facts
    no_pixels = candidate_signals(Capabilities(), "marketing",
                                  seo=SEO(meta_description_present=True), tracking=Tracking())
    assert "no_marketing_pixel" in no_pixels
