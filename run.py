#!/usr/bin/env python3
"""
Convenience runner — extract a company profile (free tier) without boilerplate.

Usage:
    python run.py https://providentestate.com
    python run.py providentestate.com --lens marketing
    python run.py https://dandbdubai.com --json
    python run.py https://example.com --no-cache --quiet

The free tier returns a profile + a *pro_features* count of opportunities. For the
verified signals, scores, offer matches, and outreach, use Autonitia Intel Pro.
"""

import argparse
import sys

from autonitia_intel import ProfileGraph
from autonitia_intel.lenses import LENSES


def _print_summary(r) -> None:
    tc = r.target_company
    line = "─" * 60
    print(f"\n{line}")
    print(f"  {tc.name or '(unknown)'}  —  {tc.industry or 'industry unknown'}")
    print(line)
    if tc.description:
        print(f"  {tc.description}")
    if tc.location:
        print(f"  Location: {tc.location}")
    if tc.contact.phones:
        print(f"  Phones:   {', '.join(tc.contact.phones[:3])}" + (" …" if len(tc.contact.phones) > 3 else ""))
    if tc.contact.emails:
        print(f"  Emails:   {', '.join(tc.contact.emails)}")
    if tc.contact.addresses:
        print(f"  Offices:  {len(tc.contact.addresses)} address(es)")

    socials = {k: v for k, v in r.digital_presence.social_media.model_dump().items() if v}
    if socials:
        print(f"  Socials:  {', '.join(socials.keys())}")

    print(f"\n  Capabilities present: {', '.join(r.capabilities_present) or 'none detected'}")
    if r.detected_tools:
        print(f"  Detected tools:       {', '.join(t.name for t in r.detected_tools)}")

    t = r.pro_features
    print(f"\n  🔒 {t.message}")
    if t.opportunities_found:
        print(f"     {t.upgrade}")
    print(line + "\n")


def main():
    parser = argparse.ArgumentParser(description="Extract a business-website profile with autonitia-intel (free).")
    parser.add_argument("url")
    parser.add_argument("--lens", default="automation", choices=LENSES)
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    graph = ProfileGraph(lens=args.lens, telemetry=False, verbose=not args.quiet)
    try:
        result = graph.run(args.url, use_cache=not args.no_cache)
    except Exception as e:
        print(f"\n✗ Analysis failed: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(result.model_dump_json(indent=2))
    else:
        _print_summary(result)


if __name__ == "__main__":
    main()
