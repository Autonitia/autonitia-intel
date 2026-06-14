"""
Example: extract a company profile with the Python API.

    python examples/analyze_example.py https://providentestate.com
"""

import sys

from autonitia_intel import ProfileGraph

url = sys.argv[1] if len(sys.argv) > 1 else "https://providentestate.com"

profile = ProfileGraph(lens="automation").run(url)
print(profile.model_dump_json(indent=2))
