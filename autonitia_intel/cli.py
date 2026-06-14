"""
CLI: autonitia-intel analyse — extract a company profile (+ opportunity pro_features).

Example:
    python -m autonitia_intel analyse --target-url https://example.com --lens automation
"""

import argparse
import sys
from pathlib import Path

from .config import OUTPUT_DIR
from .graph import ProfileGraph
from .lenses import LENSES


def main(argv=None):
    parser = argparse.ArgumentParser(prog="autonitia-intel", description="Business-website profile extractor (free tier).")
    sub = parser.add_subparsers(dest="command")

    a = sub.add_parser("analyse", help="Extract a profile from a business website")
    a.add_argument("--target-url", required=True)
    a.add_argument("--lens", default="automation", choices=LENSES, help="Lens used only for the opportunity pro_features count")
    a.add_argument("--api-key", default=None, help="Bring your own model key (overrides env)")
    a.add_argument("--model", default=None, help="Model id (overrides env)")
    a.add_argument("--no-cache", action="store_true")
    a.add_argument("--no-telemetry", action="store_true")
    a.add_argument("--quiet", action="store_true")

    args = parser.parse_args(argv)
    if args.command != "analyse":
        parser.print_help()
        sys.exit(1)

    graph = ProfileGraph(
        lens=args.lens,
        telemetry=not args.no_telemetry,
        verbose=not args.quiet,
        api_key=args.api_key,
        model=args.model,
    )
    if not args.quiet:
        print(f"Analysing {args.target_url} (lens={args.lens}) ...")
    result = graph.run(args.target_url, use_cache=not args.no_cache)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    name = (result.target_company.name or "result").replace("/", "_").replace(" ", "_")
    path = OUTPUT_DIR / f"{name}_profile.json"
    path.write_text(result.model_dump_json(indent=2))

    print(f"\nSaved: {path}\n")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
