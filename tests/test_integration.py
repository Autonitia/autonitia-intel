"""
Integration tests — run the free ProfileGraph against real websites.

Marked `integration` (network + OpenAI API); skipped by default:
    pytest -m integration            # run them
    pytest -m "not integration"      # skip

Assert robust INVARIANTS: a valid profile is extracted, the pro_features count is
sane, and contact details surface for a local business.
"""

import os

import pytest

from autonitia_intel import ProfileGraph

pytestmark = pytest.mark.integration

TARGETS = [
    "https://springfieldproperties.ae",
    "https://dandbdubai.com",
    "https://www.harleystreetdentalclinic.co.uk",
    "https://www.rush.co.uk/",
]


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="needs OPENAI_API_KEY")
@pytest.mark.parametrize("url", TARGETS)
def test_profile_graph_produces_valid_profile(url):
    graph = ProfileGraph(lens="automation", verbose=False, telemetry=False)
    result = graph.run(url, use_cache=True)

    assert result.target_company.name, f"{url}: company name should be extracted"
    assert result.target_company.domain, f"{url}: domain should be set"
    assert result.target_company.description, f"{url}: description should be extracted"

    # ProFeatures count is a sane non-negative integer
    assert result.pro_features.opportunities_found >= 0
    assert result.pro_features.lens == "automation"

    # capabilities_present is a list of known capability names
    assert isinstance(result.capabilities_present, list)


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="needs OPENAI_API_KEY")
def test_contact_details_extracted_for_local_business():
    """A dental clinic should expose a phone number or email somewhere on the site."""
    graph = ProfileGraph(lens="automation", verbose=False, telemetry=False)
    result = graph.run("https://www.harleystreetdentalclinic.co.uk", use_cache=True)
    contact = result.target_company.contact
    assert contact.phones or contact.emails, "expected at least one phone or email for a clinic"
