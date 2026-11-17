#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Rishabh Tiwari
"""Checks listings/*.json: the fields, then the repository at the pinned commit.

    scripts/check-listing.py [id ...]       the listings named (default: all)
    --no-validate                           skip `riskell-ext validate` (it runs when the tool is found: RISKELL_EXT or `riskell-ext` on PATH)
    --strict                                a missing v<version> tag is an error, not a warning

For each listing: the file name equals the id and the ids are unique; the fields have the shape the schema says; the repository is cloned and
checked out at `rev`; riskell.json there (at the repository root, or at `path` for a bundled listing) agrees on id, kind, version, license,
kit and atoms; and `riskell-ext validate` passes. Exit 1 on any error. file:// repositories are accepted only with REGISTRY_ALLOW_FILE=1 (tests).
"""
import json, os, re, shutil, subprocess, sys, tempfile, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,38}$")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$")
KINDS = {"atom", "reading", "pill", "theme", "preset"}
REQUIRED = ["id", "kind", "name", "summary", "repo", "rev", "version", "license"]
ALLOWED = set(REQUIRED) | {"$schema", "path", "kit", "atoms", "keywords", "authors", "homepage", "preview", "bundled"}
errors = warnings = 0

def err(l, m):
    global errors; errors += 1; print(f"error: {l}: {m}")
def warn(l, m):
    global warnings; warnings += 1; print(f"warning: {l}: {m}")

def fields(l, d):
    for k in REQUIRED:
        if not isinstance(d.get(k), str) or not d[k]: err(l, f'"{k}" is required (a non-empty string)')
    for k in d:
        if k not in ALLOWED: err(l, f'unknown field "{k}"')
    if isinstance(d.get("id"), str) and not ID.match(d["id"]): err(l, "id must be lowercase letters, digits and - (at most 39)")
    if d.get("kind") not in KINDS: err(l, f"kind must be one of {sorted(KINDS)}")
    if len(d.get("name", "")) > 60: err(l, "name is over 60 characters")
    if len(d.get("summary", "")) > 140: err(l, "summary is over 140 characters")
    if not re.match(r"^[0-9a-f]{40}$", d.get("rev", "")): err(l, "rev must be a full 40-character commit hash")
    if not SEMVER.match(d.get("version", "")): err(l, "version is not SemVer")
    repo = d.get("repo", "")
    if not repo.startswith("https://") and not (repo.startswith("file://") and os.environ.get("REGISTRY_ALLOW_FILE")): err(l, "repo must be an https URL")
    if "path" in d and not d.get("bundled"): err(l, '"path" is only for bundled listings: an installable extension has riskell.json at its repository root')
    if len(d.get("keywords", [])) > 10: err(l, "at most 10 keywords")

def run(args, cwd=None):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0",
               GIT_ALLOW_PROTOCOL="https:file" if os.environ.get("REGISTRY_ALLOW_FILE") else "https")      # never ext:: (it runs commands), never ssh
    if args and args[0] == "git": args = ["git", "-c", "protocol.ext.allow=never", "-c", "core.hooksPath=/dev/null"] + args[1:]
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout + p.stderr).strip()

def repository(l, d, tmp):
    dest = os.path.join(tmp, d["id"])
    rc, out = run(["git", "clone", "--quiet", "--", d["repo"], dest])
    if rc: err(l, f"cannot clone {d['repo']}: {out.splitlines()[-1] if out else rc}"); return None
    rc, out = run(["git", "checkout", "--quiet", d["rev"]], dest)      # rev is a checked 40-hex string here
    if rc: err(l, f"commit {d['rev'][:10]} is not in the repository"); return None
    rc, tags = run(["git", "tag", "--points-at", d["rev"]], dest)
    if not d.get("bundled") and f"v{d['version']}" not in tags.split():
        (err if STRICT else warn)(l, f"no tag v{d['version']} on {d['rev'][:10]}")
    return dest

def manifest(l, d, dest):
    base = os.path.join(dest, d["path"]) if d.get("path") else dest
    try: m = json.load(open(os.path.join(base, "riskell.json")))
    except Exception as e: err(l, f"no readable riskell.json at the pinned commit ({e})"); return None
    for k in ("id", "kind", "version", "license"):
        if m.get(k) != d.get(k): err(l, f'"{k}" is {d.get(k)!r} here but {m.get(k)!r} in riskell.json')
    if d.get("kit") and m.get("kit") and d["kit"] != m["kit"]: err(l, f'"kit" is {d["kit"]!r} here but {m["kit"]!r} in riskell.json')
    if d.get("atoms") is not None and m.get("atoms") is not None and sorted(d["atoms"]) != sorted(m["atoms"]): err(l, f'"atoms" differ from riskell.json: {m["atoms"]}')
    return base

def preview(l, d, dest):
    p = d.get("preview")
    if not p:
        if not d.get("bundled"): warn(l, "no preview: the storefront shows a picture of the widget (a PNG in the repository)")
        return
    f = os.path.normpath(os.path.join(dest, p))
    if not f.startswith(os.path.normpath(dest)) or not p.lower().endswith(".png") or not os.path.isfile(f): err(l, f"preview {p!r} is not a PNG in the repository at that commit"); return
    size = os.path.getsize(f)
    if size > 500_000: err(l, f"preview is {size // 1000} KB (500 KB at most)")
    head = open(f, "rb").read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n": err(l, "preview is not a PNG file"); return
    w = int.from_bytes(head[16:20], "big")
    if w < 600: err(l, f"preview is {w} px wide (at least 600)")

def validate(l, base):
    tool = os.environ.get("RISKELL_EXT") or shutil.which("riskell-ext")
    if NO_VALIDATE or not tool:
        if not NO_VALIDATE: warn(l, "riskell-ext not found: its validation was skipped")
        return
    rc, out = run([tool, "validate", base])
    if rc: err(l, "riskell-ext validate failed:\n  " + out.replace("\n", "\n  "))

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    NO_VALIDATE = "--no-validate" in sys.argv; STRICT = "--strict" in sys.argv
    files = sorted(glob.glob(os.path.join(ROOT, "listings", "*.json")))
    if args: files = [f for f in files if os.path.basename(f)[:-5] in args]
    seen = {}
    tmp = tempfile.mkdtemp(prefix="registry-")
    for f in files:
        l = os.path.basename(f)
        try: d = json.load(open(f))
        except Exception as e: err(l, f"not valid JSON ({e})"); continue
        if d.get("id") != l[:-5]: err(l, f"the file name must be <id>.json (id is {d.get('id')!r})")
        if d.get("id") in seen: err(l, "id repeats " + seen[d["id"]])
        seen[d.get("id")] = l
        n = errors; fields(l, d)
        if errors > n: continue
        dest = repository(l, d, tmp)
        if not dest: continue
        base = manifest(l, d, dest)
        preview(l, d, dest)
        if base: validate(l, base)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{len(files)} listing(s): {errors} error(s), {warnings} warning(s)")
    sys.exit(1 if errors else 0)
