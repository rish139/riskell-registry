#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Rishabh Tiwari
"""listings/*.json -> index.json, the one file `risk ext` reads. Run after check-listing.py; the CI does both on every push to main."""
import json, glob, os, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
items = []
for f in sorted(glob.glob(os.path.join(ROOT, "listings", "*.json"))):
    d = json.load(open(f)); d.pop("$schema", None); items.append(d)
out = {"version": 1, "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "listings": items}
json.dump(out, open(os.path.join(ROOT, "index.json"), "w"), indent=1, sort_keys=True); open(os.path.join(ROOT, "index.json"), "a").write("\n")
print(f"index.json: {len(items)} listings")
