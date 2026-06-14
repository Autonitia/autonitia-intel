"""
Pydantic models — the schema contract for the FREE (open-source) tier.

The open-source engine is a clean profile extractor: it returns observable
facts about a company plus a *pro_features* count of opportunities. The verified
intelligence (signals, scores, offer matching, outreach) is part of the hosted
Autonitia Intel product.

LLM response models (FactExtraction) stay flat: no dict fields.
"""

from pydantic import BaseModel, Field


# ── Provider (the company USING the tool) ──────────────────────

class CompanyProfile(BaseModel):
    """The seller/agency/solution-provider running the analysis."""
    name: str
    domain: str = ""
    company_type: str = ""
    industry: str = ""
    offers: list[str] = Field(default_factory=list)
    offer_categories: list[str] = Field(default_factory=list)
    target_customers: list[str] = Field(default_factory=list)
    target_customer_categories: list[str] = Field(default_factory=list)


# ── LLM response model (flat, no dicts) ────────────────────────

class FactExtraction(BaseModel):
    """Structured output from the fact-extraction LLM call."""
    company_name: str = ""
    industry: str = ""
    business_model: str = Field(default="", description="e.g. 'Local service business', 'SaaS', 'E-commerce'")
    services: list[str] = Field(default_factory=list)
    description: str = Field(default="", description="One-sentence summary of what the company does")
    city: str = ""
    country: str = ""
    emails: list[str] = Field(default_factory=list, description="Contact email addresses found")
    phones: list[str] = Field(default_factory=list, description="Contact phone numbers found")
    addresses: list[str] = Field(default_factory=list, description="Physical office addresses found")


# ── Detection result models (deterministic) ────────────────────

class DetectedTool(BaseModel):
    name: str
    category: str
    confidence: float
    evidence: str = ""


class SocialMedia(BaseModel):
    facebook: str = ""
    instagram: str = ""
    linkedin: str = ""
    tiktok: str = ""
    youtube: str = ""
    x: str = ""


class Capabilities(BaseModel):
    has_phone: bool = False
    has_email: bool = False
    has_contact_form: bool = False
    has_whatsapp: bool = False
    has_online_booking: bool = False
    has_live_chat: bool = False
    has_pricing: bool = False
    has_case_studies: bool = False
    has_social_links: bool = False
    has_newsletter: bool = False


class SEO(BaseModel):
    title_tag_present: bool = False
    meta_description_present: bool = False


class Tracking(BaseModel):
    google_analytics: bool = False
    google_tag_manager: bool = False
    meta_pixel: bool = False
    tiktok_pixel: bool = False
    linkedin_pixel: bool = False
    hotjar: bool = False


class Contact(BaseModel):
    """Actual reach-out details — the part a lead-gen user needs to act."""
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    whatsapp: str = ""
    addresses: list[str] = Field(default_factory=list)


class TargetCompany(BaseModel):
    name: str = ""
    domain: str = ""
    industry: str = ""
    business_model: str = ""
    description: str = ""
    location: str = ""
    services: list[str] = Field(default_factory=list)
    contact: Contact = Field(default_factory=Contact)


class DigitalPresence(BaseModel):
    social_media: SocialMedia = Field(default_factory=SocialMedia)
    seo: SEO = Field(default_factory=SEO)
    tracking: Tracking = Field(default_factory=Tracking)


# ── ProFeatures (free tier) ─────────────────────────────────────────

class ProFeatures(BaseModel):
    """
    A locked preview of the Pro intelligence: how many opportunities were
    detected (deterministically), without revealing the signals/scores/offers.
    """
    lens: str = "automation"
    opportunities_found: int = 0
    message: str = ""
    upgrade: str = "Upgrade to Autonitia Intel Pro for verified signals, scores, offer matches, and outreach."


# ── Free result ────────────────────────────────────────────────

class ProfileResult(BaseModel):
    """The output of the open-source ProfileGraph: facts + presence + pro_features."""
    target_company: TargetCompany = Field(default_factory=TargetCompany)
    digital_presence: DigitalPresence = Field(default_factory=DigitalPresence)
    capabilities_present: list[str] = Field(default_factory=list, description="Capabilities observed on the site")
    detected_tools: list[DetectedTool] = Field(default_factory=list)
    pro_features: ProFeatures = Field(default_factory=ProFeatures)
